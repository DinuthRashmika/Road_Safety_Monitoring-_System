import { useState } from 'react'
import {BrowserRouter, Route, Routes, } from 'react-router-dom'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import VideoIncoming from "./pages/video_incoming"
// import './App.css'

function App() {

  return (
    <div>
      <BrowserRouter>
        <Routes>
          <Route path='/video_incoming' element={<VideoIncoming/>} />
        </Routes>
      </BrowserRouter>
    </div>
  )
}

export default App;
