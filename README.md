# LetzRyd Cashfree Web Integration

This repository contains the web portal for LetzRyd drivers and a backend Express API server that securely creates Cashfree order sessions.

## Project Structure
- `src/`: The React (Vite) frontend containing the driver portal.
- `api-server.js`: The Express.js backend server responsible for communicating with Cashfree's `/pg/orders` API.

## Local Development Setup

### 1. Start the API Server
The API Server handles order creation using your Cashfree App ID and Secret Key.
```bash
node api-server.js
```
The server will start on `http://localhost:3001`.

### 2. Start the Frontend
In a new terminal window, start the Vite development server:
```bash
npm install
npm run dev
```
The frontend will start on `http://localhost:3002`.

## Deployment Guide

### Deploying the Backend (Render.com)
1. Create a new "Web Service" on Render and link this repository.
2. Set the Build Command to `npm install` and the Start Command to `node api-server.js`.
3. Add your Environment Variables: `APP_ID` and `SECRET_KEY` for Cashfree.

### Deploying the Frontend (Vercel)
1. Go to Vercel and import this repository.
2. Vercel will automatically detect Vite and configure the build settings.
3. **IMPORTANT**: Once your backend is deployed on Render, update the `API_URL` variable in `src/App.tsx` and `src/components/SettleScreen.tsx` to point to your new Render URL instead of `localhost:3001`.
