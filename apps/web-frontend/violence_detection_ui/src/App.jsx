import {BrowserRouter, Route, Routes, } from 'react-router-dom'
import VideoSources from "./pages/DisplayVideoSources"
import './index.css'
import Detection from './pages/DetectionMonitering';
import AlertsHistory from './pages/AlertsHistory';
import DetectionHistory from './pages/DetectionHistory';

function App() {

  return (
      <BrowserRouter>
        <Routes>
          <Route path='/' element={<VideoSources/>} />
          <Route path='/detection-monitering' element={<Detection/>} />
          <Route path='/detections' element={<DetectionHistory/>}/>
          <Route path='/alerts' element={<AlertsHistory/>}/>
        </Routes>
      </BrowserRouter>
  )
}

export default App;
