import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import ChatComponent from './ChatComponent';
import { getUser } from './api';

// FIX: session-storage key for persisting login across page refreshes
const SESSION_KEY = 'fitai_user';

function Dashboard() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const restore = async () => {
      // 1. Prefer fresh login state from React Router
      if (state?.name) {
        const userData = {
          id: state.id,
          name: state.name,
          age: state.age,
          height: state.height,
          weight: state.weight,
        };
        setUser(userData);
        // FIX: persist to sessionStorage so refresh doesn't lose the session
        sessionStorage.setItem(SESSION_KEY, JSON.stringify(userData));
        setLoading(false);
        return;
      }

      // 2. FIX: on page refresh, try to restore from sessionStorage
      const cached = sessionStorage.getItem(SESSION_KEY);
      if (cached) {
        try {
          const parsed = JSON.parse(cached);
          // Re-validate against the server to make sure the user still exists
          const res = await getUser(parsed.id);
          setUser(res.data);
          setLoading(false);
          return;
        } catch {
          sessionStorage.removeItem(SESSION_KEY);
        }
      }

      // 3. No valid session — send back to login
      navigate('/');
    };

    restore();
  }, [state, navigate]);

  const handleSignOut = () => {
    sessionStorage.removeItem(SESSION_KEY);
    navigate('/');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <p className="text-slate-400 text-lg animate-pulse">Loading your dashboard...</p>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="min-h-screen bg-slate-50 relative flex flex-col items-center p-6 transition-all duration-500">
      {/* Background blobs */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10 bg-white">
        <div className="absolute top-[10%] right-[10%] w-[500px] h-[500px] bg-blue-100 rounded-full mix-blend-multiply filter blur-3xl opacity-50 animate-blob" />
        <div className="absolute bottom-[10%] left-[10%] w-[500px] h-[500px] bg-purple-100 rounded-full mix-blend-multiply filter blur-3xl opacity-50 animate-blob animation-delay-2000" />
      </div>

      <div className="w-full max-w-6xl mx-auto flex flex-col gap-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-center bg-white/60 backdrop-blur-md p-8 rounded-3xl border border-white/40 shadow-sm">
          <div>
            <h1 className="text-4xl font-extrabold text-slate-800 mb-1">
              Hello,{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">
                {user.name}
              </span>{' '}
              👋
            </h1>
            <p className="text-slate-500 font-medium tracking-wide">
              WELCOME BACK TO YOUR PERSONAL HUB
            </p>
          </div>
          <button
            onClick={handleSignOut}
            className="mt-4 md:mt-0 px-6 py-2 bg-white text-slate-600 font-semibold rounded-full border border-slate-200 hover:bg-slate-50 hover:text-red-500 transition-all shadow-sm"
          >
            Sign Out
          </button>
        </div>

        {/* Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Stats Card */}
          <div className="bg-white p-8 rounded-3xl shadow-[0_4px_20px_rgb(0,0,0,0.03)] border border-slate-100 flex flex-col justify-between h-full">
            <h2 className="text-xl font-bold text-slate-800 mb-6 flex items-center gap-2">
              <span className="w-2 h-6 bg-blue-500 rounded-full" />
              Your Metrics
            </h2>
            <div className="space-y-6">
              {[
                { label: 'Age', value: `${user.age}`, unit: 'yrs' },
                { label: 'Height', value: user.height },
                { label: 'Weight', value: user.weight },
              ].map(({ label, value, unit }) => (
                <div
                  key={label}
                  className="flex justify-between items-center p-4 bg-slate-50 rounded-2xl"
                >
                  <span className="text-slate-500 font-medium">{label}</span>
                  <span className="text-2xl font-bold text-slate-800">
                    {value}{' '}
                    {unit && (
                      <span className="text-sm font-normal text-slate-400">{unit}</span>
                    )}
                  </span>
                </div>
              ))}
            </div>
            <div className="mt-8 p-4 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl text-white text-center">
              <p className="text-sm opacity-80 mb-1">Plan Status</p>
              <p className="font-bold text-lg">Active</p>
            </div>
          </div>

          {/* Chat — FIX: no longer passes age/height/weight; backend fetches them */}
          <div className="lg:col-span-2">
            <ChatComponent name={user.name} faceId={user.id} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
