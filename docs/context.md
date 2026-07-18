# Project Context: AI-Powered Restaurant Recommendation System

## Overview

This project is an **AI-powered restaurant recommendation service** inspired by Zomato. It combines structured restaurant data with a Large Language Model (LLM) to deliver personalized, human-like restaurant suggestions based on user preferences.

## Objective

Design and implement an application that:

- Takes user preferences (location, budget, cuisine, ratings, and more)
- Uses a real-world dataset of restaurants
- Leverages an LLM to generate personalized, human-like recommendations
- Displays clear and useful results to the user

## Data Source

| Property | Value |
|----------|-------|
| **Dataset** | Zomato Restaurant Recommendation |
| **Provider** | Hugging Face |
| **URL** | https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation |

### Relevant Fields

Extract and use fields such as:

- Restaurant name
- Location
- Cuisine
- Cost
- Rating
- (Other fields as available in the dataset)

## User Input

Collect the following preferences from the user:

| Preference | Examples / Notes |
|------------|------------------|
| **Location** | Delhi, Bangalore |
| **Budget** | Low, medium, high |
| **Cuisine** | Italian, Chinese, etc. |
| **Minimum rating** | Numeric threshold |
| **Additional preferences** | Family-friendly, quick service, etc. |

## System Workflow

### 1. Data Ingestion

- Load and preprocess the Zomato dataset from Hugging Face
- Extract relevant fields (name, location, cuisine, cost, rating, etc.)

### 2. User Input

- Collect user preferences via the application interface
- Support location, budget, cuisine, minimum rating, and optional free-form preferences

### 3. Integration Layer

- Filter and prepare relevant restaurant data based on user input
- Pass structured results into an LLM prompt
- Design a prompt that helps the LLM reason and rank options

### 4. Recommendation Engine

Use the LLM to:

- Rank restaurants by fit to user preferences
- Provide explanations for why each recommendation fits
- Optionally summarize the overall set of choices

### 5. Output Display

Present top recommendations in a user-friendly format. Each result should include:

- Restaurant name
- Cuisine
- Rating
- Estimated cost
- AI-generated explanation

## Architecture Summary

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  User Input │────▶│ Integration Layer│────▶│ Recommendation  │
│ (preferences)│     │ (filter + prompt)│     │ Engine (LLM)    │
└─────────────┘     └────────┬─────────┘     └────────┬────────┘
                             │                        │
                    ┌────────▼─────────┐              │
                    │ Zomato Dataset   │              │
                    │ (Hugging Face)   │              │
                    └──────────────────┘              │
                                                      ▼
                                            ┌─────────────────┐
                                            │ Output Display  │
                                            │ (ranked results)│
                                            └─────────────────┘
```

## Key Design Decisions (To Be Made)

- **LLM provider and model** — OpenAI, Anthropic, local model, etc.
- **Application type** — CLI, web app, API, or combination
- **Filtering strategy** — Pre-filter dataset before LLM vs. pass broader context to LLM
- **Prompt design** — Structure for ranking, explanation, and optional summary
- **Number of recommendations** — How many top results to show

## Success Criteria

- [ ] Dataset loads and preprocesses correctly from Hugging Face
- [ ] User can specify location, budget, cuisine, rating, and optional preferences
- [ ] System filters data based on user input before LLM processing
- [ ] LLM ranks restaurants and generates meaningful explanations
- [ ] Results are displayed clearly with name, cuisine, rating, cost, and explanation

## Reference

- Source problem statement: [`problemstatement.txt`](./problemstatement.txt)
