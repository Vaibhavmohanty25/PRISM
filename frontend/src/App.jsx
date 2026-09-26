import {
    BrowserRouter,
    Routes,
    Route,
  } from "react-router-dom";
  
  import AppLayout from "./components/layout/AppLayout";
  
  import Dashboard from "./pages/Dashboard";
  import UploadReport from "./pages/UploadReport";
  import Projects from "./pages/Projects";
  import ProjectDetails from "./pages/ProjectDetails";
  import AgentWorkspace from "./pages/AgentWorkspace";
  
  export default function App() {
    return (
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route
              path="/"
              element={<Dashboard />}
            />
  
            <Route
              path="/upload"
              element={<UploadReport />}
            />
  
            <Route
              path="/projects"
              element={<Projects />}
            />
  
            <Route
              path="/projects/:projectName"
              element={<ProjectDetails />}
            />
  
            <Route
              path="/agent"
              element={<AgentWorkspace />}
            />
          </Route>
        </Routes>
      </BrowserRouter>
    );
  }