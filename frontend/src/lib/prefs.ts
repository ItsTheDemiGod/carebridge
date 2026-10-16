/* The ONLY two things the frontend stores in localStorage: language and calm mode. Both non-sensitive. */
const KEYS = { language: 'carebridge.language', calm: 'carebridge.calm' } as const

export function readPref(name: keyof typeof KEYS): string | null {
  try {
    return localStorage.getItem(KEYS[name])
  } catch {
    return null
  }
}

export function writePref(name: keyof typeof KEYS, value: string): void {
  try {
    localStorage.setItem(KEYS[name], value)
  } catch {
    /* storage unavailable: the preference simply is not remembered */
  }
}
