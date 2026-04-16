import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Send, Sparkles } from 'lucide-react'
import { fetchPropertyExplainChatHistory, sendPropertyExplainChatMessage } from '../api/ai'
import { formatApiError } from '../lib/format'

type Bubble = {
  key: string
  role: 'user' | 'assistant'
  content: string
}

export function PropertyExplainPage() {
  const { id } = useParams<{ id: string }>()
  const pid = Number(id)
  const [messages, setMessages] = useState<Bubble[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!Number.isFinite(pid)) return
    let cancelled = false
    void (async () => {
      try {
        const { results } = await fetchPropertyExplainChatHistory(pid, 80)
        if (cancelled) return
        setMessages(
          results.map((m) => ({
            key: `srv-${m.id}`,
            role: m.role,
            content: m.content,
          }))
        )
      } catch {
        /* ignore history errors */
      }
    })()
    return () => {
      cancelled = true
    }
  }, [pid])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const onSend = async (e: React.FormEvent) => {
    e.preventDefault()
    const text = input.trim()
    if (!text || loading || !Number.isFinite(pid)) return
    setInput('')
    setError(null)
    setMessages((m) => [...m, { key: `tmp-user-${Date.now()}-${Math.random()}`, role: 'user', content: text }])
    setLoading(true)
    try {
      const res = await sendPropertyExplainChatMessage(pid, text)
      setMessages((m) => [
        ...m,
        {
          key: `tmp-asst-${Date.now()}-${Math.random()}`,
          role: 'assistant',
          content: res.assistant_message,
        },
      ])
    } catch (err) {
      setError(formatApiError(err))
      setMessages((m) => [
        ...m,
        {
          key: `tmp-asst-err-${Date.now()}-${Math.random()}`,
          role: 'assistant',
          content: 'Не вдалося отримати відповідь. Спробуйте ще раз.',
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto flex max-w-3xl flex-col px-4 py-10" style={{ minHeight: '70vh' }}>
      <Link to={`/properties/${id}`} className="text-sm text-brand-dark underline">
        ← До оголошення
      </Link>
      <div className="mt-6 flex items-center gap-2">
        <Sparkles className="h-8 w-8 text-brand" />
        <h1 className="font-display text-2xl font-semibold text-slate-900">
          AI чат-пояснення для об’єкта #{id}
        </h1>
      </div>

      {error && (
        <div className="mt-6 rounded-xl border border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-900">
          {error}
        </div>
      )}

      <div className="mt-6 flex-1 space-y-4 overflow-y-auto rounded-3xl border border-slate-100 bg-white p-4 shadow-sm">
        {messages.length === 0 && (
          <p className="text-center text-sm text-slate-500">
            Напишіть, наприклад: «Які тут мінуси?», «Скільки приблизно комунальні?», «Чи норм для студента?»
          </p>
        )}
        {messages.map((msg) => (
          <div key={msg.key} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm ${
                msg.role === 'user' ? 'bg-brand text-white' : 'bg-slate-100 text-slate-800'
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.content}</p>
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={(e) => void onSend(e)} className="mt-4 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ваше повідомлення…"
          className="flex-1 rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-brand/30"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading}
          className="inline-flex items-center justify-center rounded-2xl bg-accent px-5 text-white hover:bg-accent-hover disabled:opacity-60"
        >
          <Send className="h-5 w-5" />
        </button>
      </form>
    </div>
  )
}
