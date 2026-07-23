import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { useGameStore } from "./store";
import "./index.css";

// Expose store for E2E testing (dev only)
if (import.meta.env.DEV) {
  (window as unknown as Record<string, unknown>).__ZUSTAND_STORE__ = useGameStore;
}

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Root element not found");
}

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
