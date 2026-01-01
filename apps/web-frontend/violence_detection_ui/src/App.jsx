// import { useState } from 'react'
import {BrowserRouter, Route, Routes, } from 'react-router-dom'
// import reactLogo from './assets/react.svg'
// import viteLogo from '/vite.svg'
import VideoSources from "./pages/video_sources"
// import './App.css'

function App() {

  return (
      <BrowserRouter>
        <Routes>
          <Route path='/' element={<VideoSources/>} />
          {/* <Route path='/video_incoming' element={<VideoIncoming/>} /> */}
        </Routes>
      </BrowserRouter>
  )
}

export default App;
