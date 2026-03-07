import Navbar from './Navbar'

export default function Layout({ children }) {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar />
      <main style={{ flex: 1, padding: '2.5rem 3rem', maxWidth: '1200px', width: '100%', margin: '0 auto' }} className="page-enter">
        {children}
      </main>
    </div>
  )
}