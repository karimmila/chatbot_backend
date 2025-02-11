# Chatbot Assistant Documentation

[Deployed frontend Link](https://mango-wave-07f8b9f10.4.azurestaticapps.net/)

## 1. Project Overview

### Approach and Solution

Creating this chatbot assistant was all about making it smart, fast, and reliable in answering questions about the Promtior website. To achieve this, we leveraged Retrieval-Augmented Generation (RAG)—a method that combines searching for relevant documents with AI-powered text generation.

At its core, the chatbot works by finding the right pieces of information from Markdown and PDF files, thanks to FAISS (a vector database), and then using OpenAI's GPT-4o model to generate human-like responses. It’s packaged as a REST API using LangServe and FastAPI, making it easy to integrate into any frontend application.

Additionally, for scraping data from the Promtior website, we used Firecrawl—a tool that automates web crawling and data extraction, making it easier to collect structured information from web pages.

### How It Works

1. Processing the Data

   - The chatbot first loads documents (Markdown and PDFs) using TextLoader and PyPDFLoader.

   - It breaks these documents into smaller chunks using RecursiveCharacterTextSplitter, so it can find precise answers.

2. Storing the Knowledge

   - Each document chunk is converted into vector embeddings using OpenAI's text-embedding-3-large.

   - The embeddings are stored in FAISS, allowing the chatbot to quickly search for the most relevant snippets.

3. Retrieving and Generating Answers

   - When a user asks a question, the LangServe API receives the request.

   - The chatbot searches FAISS to find relevant pieces of text.

   - ChatOpenAI (GPT-4o-mini) takes this retrieved information and crafts a response.

4. Deploying the Chatbot

   - The FastAPI server ensures the chatbot is accessible through a simple API endpoint.

   - The backend is deployed in azure App Service, while the frontend is deployed in a Static Web App. Both using Contious integration when pushed to main branch.

### Challenges & How We Solved Them

- Getting Accurate Answers

  - Issue: Sometimes, the chatbot gave vague or incorrect responses.

  - Fix: Tweaked how many document chunks it retrieves (k=10), ensuring the AI gets enough context before answering.

- Speeding Up Responses

  - Issue: The chatbot was taking too long to respond.

  - Fix: Reduced chunk size and overlap, optimized FAISS retrieval, and adjusted OpenAI API parameters for efficiency.

- Making It Easy to Deploy

  - Issue: The chatbot needed to work smoothly across different platforms.

  - Fix: Used LangServe for a structured REST API, and opted for a direct cloud deployment instead of using Docker.

## 2. Component Diagram

The following diagram shows how everything works together when a user asks a question:

![image info](./diagram.png)

#### Diagram Breakdown

- User Interaction: A user sends a question through the chatbot interface.

- FastAPI & LangServe: The API processes the request and forwards it to the retrieval system.

- Searching for Information: FAISS scans stored documents and finds the most relevant content.

- Generating an Answer: ChatOpenAI (GPT-4o-mini) formulates a response based on the retrieved text.

- Delivering the Response: The chatbot sends the answer back to the user.
