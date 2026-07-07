module.exports = {
  apps: [
    {
      name: "agent-api",
      cwd: "./api",
      script: "./.venv/bin/uvicorn",
      args: "main:app --host 0.0.0.0 --port 8000",
      interpreter: "none",
      env: {
        NODE_ENV: "production"
      }
    },
    {
      name: "agent-whatsapp",
      cwd: "./whatsapp",
      script: "dist/index.js",
      interpreter: "node",
      env: {
        NODE_ENV: "production"
      }
    }
  ]
};
