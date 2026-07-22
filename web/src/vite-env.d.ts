/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_LIFF_ID?: string;
  readonly VITE_LIFF_IDENTITY_ENABLED?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
