import { useNavigate } from 'react-router-dom'
import { createProperty } from '../api/properties'
import { formatApiError } from '../lib/format'
import { PropertyForm, defaultEmptyProperty } from '../components/PropertyForm'

export function PropertyCreatePage() {
  const navigate = useNavigate()

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="font-display text-3xl font-semibold text-slate-900">
        Нове оголошення
      </h1>
      <p className="mt-2 text-slate-600">Заповніть поля та додайте локацію й фото.</p>
      <div className="mt-8">
        <PropertyForm
          initial={defaultEmptyProperty()}
          submitLabel="Опублікувати"
          onCancel={() => navigate(-1)}
          onSubmit={async (payload) => {
            try {
              const created = await createProperty(payload)
              navigate(`/properties/${created.id}`, { replace: true })
            } catch (e) {
              throw new Error(formatApiError(e))
            }
          }}
        />
      </div>
    </div>
  )
}
