---
title: Gemini Live Agent Challenge
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
app_file: Dockerfile
pinned: false
---

# AI Multimodal Tutor

An AI-powered tutor that transforms any GitHub programming course into an interactive learning assistant using RAG + Gemini LLM.

## Features

- GitHub Repo Input - Enter any public repo URL to learn from it
- Voice & Text Input - Ask questions via voice or text
- Smart Responses - AI-generated answers grounded in course material
- Code Highlighting - Beautiful syntax-highlighted code examples
- Voice Output - Listen to answers via Text-to-Speech

## Deployment

### GitHub Repository
- **URL**: https://github.com/Abdullah-9862873/Gemini-Live-Agent-Challenge

### Backend - Hugging Face Spaces
- **URL**: https://abdullah9862873-gemini-live-agent-challenge.hf.space
- **Platform**: Hugging Face Spaces (Docker)
- **Environment Variables**:
  - PINECONE_API_KEY
  - GEMINI_API_KEY
  - PINECONE_INDEX_NAME = course-vectors
  - PINECONE_ENVIRONMENT = us-east-1

### Frontend - Vercel
- **URL**: https://gemini-live-agent-challenge.vercel.app
- **Platform**: Vercel (Next.js)
- **Environment Variables**:
  - NEXT_PUBLIC_API_URL = https://abdullah9862873-gemini-live-agent-challenge.hf.space
