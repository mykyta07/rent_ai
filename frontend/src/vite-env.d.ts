/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_HERO_IMAGE_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
