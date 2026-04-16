import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { Send, Sparkles } from 'lucide-react'
import { fetchChatHistory, sendChatMessage } from '../api/ai'
import type { ChatHistoryMessage } from '../api/types'
import { formatApiError } from '../lib/format'

type Bubble = {
  key: string
  role: 'user' | 'assistant'
  content: string
  properties?: number[]
}

function formatAssistantText(content: string): string {
  const normalized = content.replace(/\r\n/g, '\n').replace(/\r/g, '\n')
  const lines = normalized.split('\n').map((raw) => {
    let line = raw.trim()
    if (!line) return ''
    line = line.replace(/`/g, '')
    line = line.replace(/\*\*(.*?)\*\*/g, '$1')
    line = line.replace(/__(.*?)__/g, '$1')
    line = line.replace(/^#{1,6}\s*/, '')
    if (line.startsWith('- ') || line.startsWith('* ')) {
      line = `• ${line.slice(2).trim()}`
    }
    return line
  })
  return lines.join('\n').replace(/\n{3,}/g, '\n\n').trim()
}

export function AIChatPage() {
  const [messages, setMessages] = useState<Bubble[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let cancelled = false
    void (async () => {
      try {
        const { results } = await fetchChatHistory(50)
        if (cancelled) return
        setMessages(
          results.map((m: ChatHistoryMessage) => ({
            key: `srv-${m.id}`,
            role: m.role,
            content: m.content,
            properties: m.properties ?? [],
          }))
        )
      } catch {
        /* ignore history errors */
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const onSend = async (e: React.FormEvent) => {
    e.preventDefault()
    const text = input.trim()
    if (!text || loading) return
    setInput('')
    setError(null)
    setMessages((m) => [...m, { key: `tmp-user-${Date.now()}-${Math.random()}`, role: 'user', content: text }])
    setLoading(true)
    try {
      const res = await sendChatMessage(text)
      const props = (res.properties ?? []).filter((v) => Number.isFinite(v) && v > 0)
      setMessages((m) => [
        ...m,
        {
          key: `tmp-asst-${Date.now()}-${Math.random()}`,
          role: 'assistant',
          content: res.assistant_message,
          properties: props,
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
    <div className="mx-auto flex max-w-3xl flex-col px-4 py-8" style={{ minHeight: '70vh' }}>
      <div className="mb-6 flex items-center gap-2">
        <Sparkles className="h-7 w-7 text-brand" />
        <div>
          <h1 className="font-display text-2xl font-semibold text-slate-900">AI асистент</h1>
          <p className="text-sm text-slate-600">Опишіть бажане житло українською або англійською.</p>
        </div>
      </div>

      {error && (
        <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-900">
          {error}
        </div>
      )}

      <div className="flex-1 space-y-4 overflow-y-auto rounded-3xl border border-slate-100 bg-white p-4 shadow-sm">
        {messages.length === 0 && (
          <p className="text-center text-sm text-slate-500">
            Напишіть, наприклад: «2-кімнатна квартира в Києві до $80k».
          </p>
        )}
        {messages.map((msg) => (
          <div
            key={msg.key}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm ${
                msg.role === 'user'
                  ? 'bg-brand text-white'
                  : 'bg-slate-100 text-slate-800'
              }`}
            >
              <p className="whitespace-pre-wrap">
                {msg.role === 'assistant' ? formatAssistantText(msg.content) : msg.content}
              </p>
              {msg.properties && msg.properties.length > 0 && (
                <div className="mt-3 border-t border-slate-200/50 pt-3">
                  <p className="text-xs font-semibold opacity-80">Рекомендовані ID:</p>
                  <ul className="mt-1 flex flex-wrap gap-2">
                    {msg.properties.map((id) => (
                      <li key={id}>
                        <Link
                          to={`/properties/${id}`}
                          className="rounded-full bg-white/90 px-2 py-0.5 text-xs font-medium text-brand-dark underline"
                        >
                          Об’єкт #{id}
                        </Link>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
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
