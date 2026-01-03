import React, { useState, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import { registerFace, recognizeFace } from './api';
import Dashboard from './Dashboard';

function Home() {
  const [mode, setMode] = useState('home');
  const [name, setName] = useState('');
  const [age, setAge] = useState('');
  const [height, setHeight] = useState('');
  const [weight, setWeight] = useState('');
  const [message, setMessage] = useState('');
  const webcamRef = useRef(null);
  const [imgSrc, setImgSrc] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const capture = useCallback(() => {
    const imageSrc = webcamRef.current.getScreenshot();
    setImgSrc(imageSrc);
  }, [webcamRef]);

  const retake = () => {
    setImgSrc(null);
    setMessage('');
  };

  const dataURLtoFile = (dataurl, filename) => {
    let arr = dataurl.split(','), mime = arr[0].match(/:(.*?);/)[1],
      bstr = atob(arr[1]), n = bstr.length, u8arr = new Uint8Array(n);
    while (n--) {
      u8arr[n] = bstr.charCodeAt(n);
    }
    return new File([u8arr], filename, { type: mime });
  }

  const handleRegister = async () => {
    if (!name || !age || !height || !weight || !imgSrc) return;
    setIsLoading(true);
    try {
      const file = dataURLtoFile(imgSrc, 'face.jpg');
      const res = await registerFace(name, age, height, weight, file);
      setMessage(res.data.message);
      setImgSrc(null);
      setName('');
      setAge('');
      setHeight('');
      setWeight('');
      setMode('home');
    } catch (error) {
      setMessage("Error: " + (error.response?.data?.detail || error.message));
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogin = async () => {
    if (!imgSrc) return;
    setIsLoading(true);
    try {
      const file = dataURLtoFile(imgSrc, 'query.jpg');
      const res = await recognizeFace(file);
      if (res.data.match) {
        navigate('/dashboard', {
          state: {
            name: res.data.name,
            age: res.data.age,
            height: res.data.height,
            weight: res.data.weight,
            id: res.data.id
          }
        });
      } else {
        setMessage("Unknown face. Please try again or register.");
      }
    } catch (error) {
      setMessage("Error: " + (error.response?.data?.detail || error.message));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4 relative overflow-hidden">
      {/* Cheerful Animated Background */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10">
        <div className="absolute top-[-10%] right-[-5%] w-96 h-96 bg-purple-300 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob"></div>
        <div className="absolute top-[-10%] left-[-5%] w-96 h-96 bg-yellow-300 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-2000"></div>
        <div className="absolute bottom-[-10%] left-[20%] w-96 h-96 bg-pink-300 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-4000"></div>
      </div>

      <h1 className="text-5xl font-extrabold mb-10 bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent drop-shadow-sm">
        FitAi
      </h1>

      <div className="w-full max-w-lg bg-white/80 backdrop-blur-xl rounded-3xl p-8 shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-white/20 transition-all duration-300 hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)]">
        {mode === 'home' && (
          <div className="flex flex-col gap-6">
            <div className="text-center mb-2">
              <p className="text-xl font-medium text-gray-700">Welcome Back!</p>
              <p className="text-gray-500 text-sm">Secure, fast, and personal.</p>
            </div>

            <button
              onClick={() => setMode('login')}
              className="group relative w-full flex justify-center py-4 px-4 border border-transparent text-lg font-bold rounded-2xl text-white bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 shadow-lg transform transition-all hover:-translate-y-1"
            >
              Login with Face
            </button>

            <div className="relative flex py-2 items-center">
              <div className="flex-grow border-t border-gray-200"></div>
              <span className="flex-shrink-0 mx-4 text-gray-400 text-xs uppercase">Or</span>
              <div className="flex-grow border-t border-gray-200"></div>
            </div>

            <button
              onClick={() => setMode('register')}
              className="w-full flex justify-center py-3 px-4 border-2 border-gray-200 text-lg font-semibold rounded-2xl text-gray-600 bg-transparent hover:bg-gray-50 hover:border-gray-300 focus:outline-none transition-all"
            >
              Register New User
            </button>
          </div>
        )}

        {(mode === 'register' || mode === 'login') && (
          <div className="flex flex-col gap-5 animate-fadeIn">
            <h2 className="text-2xl font-bold text-center text-gray-800 mb-2">
              {mode === 'login' ? 'Smile for the Camera! 📸' : 'Create Your Profile ✨'}
            </h2>

            <div className="relative rounded-2xl overflow-hidden bg-gray-100 aspect-video flex items-center justify-center shadow-inner border border-gray-200">
              {imgSrc ? (
                <img src={imgSrc} alt="captured" className="w-full h-full object-cover" />
              ) : (
                <Webcam
                  audio={false}
                  ref={webcamRef}
                  screenshotFormat="image/jpeg"
                  className="w-full h-full object-cover"
                />
              )}
            </div>

            {mode === 'register' && !imgSrc && (
              <div className="space-y-4">
                <div className="relative">
                  <input
                    type="text"
                    placeholder="Full Name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full px-5 py-3 rounded-xl bg-gray-50 border border-gray-200 text-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all placeholder-gray-400"
                  />
                </div>
                <div className="flex gap-3">
                  <input
                    type="number"
                    placeholder="Age"
                    value={age}
                    onChange={(e) => setAge(e.target.value)}
                    className="w-1/3 px-5 py-3 rounded-xl bg-gray-50 border border-gray-200 text-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all placeholder-gray-400"
                  />
                  <input
                    type="text"
                    placeholder="Height"
                    value={height}
                    onChange={(e) => setHeight(e.target.value)}
                    className="w-1/3 px-5 py-3 rounded-xl bg-gray-50 border border-gray-200 text-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all placeholder-gray-400"
                  />
                  <input
                    type="text"
                    placeholder="Weight"
                    value={weight}
                    onChange={(e) => setWeight(e.target.value)}
                    className="w-1/3 px-5 py-3 rounded-xl bg-gray-50 border border-gray-200 text-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all placeholder-gray-400"
                  />
                </div>
              </div>
            )}

            <div className="flex gap-3 mt-2">
              {!imgSrc ? (
                <button
                  onClick={capture}
                  className="flex-1 bg-blue-500 hover:bg-blue-600 text-white py-3 rounded-xl font-bold shadow-md hover:shadow-lg transition-all transform hover:-translate-y-0.5"
                >
                  Capture
                </button>
              ) : (
                <>
                  <button
                    onClick={retake}
                    className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-700 py-3 rounded-xl font-bold transition-all"
                  >
                    Retake
                  </button>
                  {mode === 'register' ? (
                    <button
                      onClick={handleRegister}
                      disabled={isLoading || !name || !age || !height || !weight}
                      className="flex-1 bg-gradient-to-r from-pink-500 to-rose-500 hover:from-pink-600 hover:to-rose-600 text-white py-3 rounded-xl font-bold shadow-md disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    >
                      {isLoading ? 'Saving...' : 'Register'}
                    </button>
                  ) : (
                    <button
                      onClick={handleLogin}
                      disabled={isLoading}
                      className="flex-1 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white py-3 rounded-xl font-bold shadow-md disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    >
                      {isLoading ? 'Checking...' : 'Login'}
                    </button>
                  )}
                </>
              )}
            </div>

            <button
              onClick={() => {
                setMode('home');
                setMessage('');
                setImgSrc(null);
                setName('');
                setAge('');
                setHeight('');
                setWeight('');
              }}
              className="text-gray-400 hover:text-gray-600 text-sm mt-2 text-center transition-colors"
            >
              Cancel
            </button>

            {message && (
              <div className={`p-4 rounded-xl text-center font-medium animate-bounce-short shadow-sm ${message.includes('Error') || message.includes('Unknown')
                ? 'bg-red-50 text-red-600 border border-red-100'
                : 'bg-green-50 text-green-600 border border-green-100'
                }`}>
                {message}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function App() {
  return (
    <Router basename={import.meta.env.BASE_URL}>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </Router>
  );
}

export default App;
