import {BrowserRouter, Route, Routes, } from 'react-router-dom'
import VideoSources from "./pages/VideoSources"
import './index.css'
import Detection from './pages/DetectionMonitering';

function App() {

  return (
      <BrowserRouter>
        <Routes>
          <Route path='/' element={<VideoSources/>} />
          <Route path='/detection-monitering' element={<Detection/>} />
        </Routes>
      </BrowserRouter>
  )
}

export default App;
