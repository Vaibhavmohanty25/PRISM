import axios from "axios";

const prismApi = axios.create({
  baseURL: "http://127.0.0.1:8000",
  timeout: 120000,
});

export const getProjects = async () => {
  const response = await prismApi.get(
    "/api/v1/projects"
  );

  return response.data;
};

export const uploadReport = async (file) => {
  const formData = new FormData();

  formData.append("file", file);

  const response = await prismApi.post(
    "/api/v1/upload",
    formData
  );

  return response.data;
};

export const askAgent = async (query) => {
  const response = await prismApi.post(
    "/api/v1/agent/query",
    {
      query,
    }
  );

  return response.data;
};

export const getProjectPredictiveSummary = async (
  projectName
) => {
  const response = await prismApi.get(
    `/api/v1/projects/${encodeURIComponent(
      projectName
    )}/predictive-summary`
  );

  return response.data;
};

export default prismApi;