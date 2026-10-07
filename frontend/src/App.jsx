import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth.jsx";
import Layout from "./components/Layout.jsx";
import { Spinner, ErrorBox } from "./components/Spinner.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Checkin from "./pages/Checkin.jsx";
import Result from "./pages/Result.jsx";
import Weekly from "./pages/Weekly.jsx";
import Insights from "./pages/Insights.jsx";
import Profile from "./pages/Profile.jsx";
import Settings from "./pages/Settings.jsx";

function Protected({ children }) {
  const { user, loading, bootError, retry } = useAuth();
  if (loading) return <Spinner />;
  if (!user && bootError) {
    // Token is still stored; the server just couldn't be reached. Offer a retry instead of logging out.
    return <div className="page"><ErrorBox error={bootError} onRetry={retry} /></div>;
  }
  return user ? children : <Navigate to="/login" replace />;
}

function GuestOnly({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <Spinner />;
  return user ? <Navigate to="/" replace /> : children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<GuestOnly><Login /></GuestOnly>} />
      <Route path="/register" element={<GuestOnly><Register /></GuestOnly>} />
      <Route element={<Protected><Layout /></Protected>}>
        <Route index element={<Dashboard />} />
        <Route path="checkin" element={<Checkin />} />
        <Route path="result" element={<Result />} />
        <Route path="weekly" element={<Weekly />} />
        <Route path="insights" element={<Insights />} />
        <Route path="profile" element={<Profile />} />
        <Route path="settings" element={<Settings />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
