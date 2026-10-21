import { AppRouter } from './app/router'
import DesktopStartupGate from './desktop/DesktopStartupGate'

function App() {
  return <DesktopStartupGate><AppRouter /></DesktopStartupGate>
}

export default App
