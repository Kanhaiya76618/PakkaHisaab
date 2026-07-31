import React from 'react'
import './globals.css'

export const metadata = {
  title: 'Udhaar Book',
  description: 'Credit ledger for small shop owners',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const [lang, setLang] = React.useState<'en' | 'hi'>('en')
  const toggleLang = () => setLang(prev => (prev === 'en' ? 'hi' : 'en'))
  return (
    <html lang={lang === 'en' ? 'en' : 'hi'} className={lang === 'en' ? '' : 'bg-gray-100'}>
      <body className="bg-background text-foreground min-h-screen flex flex-col">
        <header className="p-4 flex justify-between items-center bg-primary text-white">
          <h1 className="text-xl font-bold">Udhaar Book</h1>
          <button onClick={toggleLang} className="px-2 py-1 bg-accent rounded">
            {lang === 'en' ? 'हिंदी' : 'EN'}
          </button>
        </header>
        <main className="flex-1 p-4">{children}</main>
        <footer className="p-4 text-center text-sm text-gray-600">
          © {new Date().getFullYear()} Udhaar Book
        </footer>
      </body>
    </html>
  )
}
