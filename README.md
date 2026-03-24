# MealGraph — Intelligent Meal & Nutrition Optimization Engine

## Overview

MealGraph is a production-style AI system that generates optimized meal recommendations based on:

* Pantry ingredients
* Nutritional goals (e.g., high protein, low saturated fat)
* Time and budget constraints
* Personal preferences

Unlike traditional recipe apps, MealGraph combines **deterministic optimization**, **machine learning**, and **LLM-powered reasoning** to deliver explainable, adaptive meal planning.

---

## Project Architecture

MealGraph is designed as a multi-layer intelligent system:

### Optimization & ML (Deterministic Core)

* Recipe ingestion and normalization
* Ingredient → nutrition mapping (USDA FoodData Central)
* Meal ranking engine based on:

  * macro targets (protein, calories)
  * health constraints (saturated fat, sodium)
  * pantry overlap
  * prep time

### LLM Augmentation

* Natural language explanations:

  * “Why this meal?”
* Ingredient substitution:

  * “Replace missing ingredients”
* Conversational refinement:

  * “Make this cheaper / higher protein”

### Agentic System

* Planner Agent → generates meal plans
* Validator Agent → enforces constraints
* Repair Agent → fixes invalid plans

This creates a **self-correcting AI system**, similar to real-world production AI workflows.

---

## Tech Stack

### Backend

* ASP.NET Core (.NET 8) / FastAPI
* REST APIs

### Data & ML

* Python (Pandas, scikit-learn, LightGBM/XGBoost)
* PostgreSQL

### LLM Layer

* OpenAI API (structured outputs + tool calling)

### Agent Orchestration

* OpenAI Agents SDK / LangGraph

### Infrastructure

* Docker
* AWS (ECS / Fargate, RDS)

---

## Data Sources

* Food.com Recipes Dataset (Kaggle)
* USDA FoodData Central (nutrition data)

---

## Core Features

* Intelligent meal ranking engine
* Nutrition-aware filtering and scoring
* Pantry-based recommendations
* Ingredient substitution system
* Explainable AI outputs
* Multi-agent validation workflow

---

## Example Use Case

Input:

```
Pantry: chicken, rice, broccoli  
Goal: high protein, low saturated fat  
Time: < 30 minutes
```

Output:

```
1. Chicken & Broccoli Stir Fry  
   - Protein: 42g  
   - Calories: 520  
   - Missing: soy sauce  

Reason:
High protein, low saturated fat, minimal missing ingredients
```

---

## Getting Started

### 1. Clone repo

```bash
git clone https://github.com/SamJamZzz/MealGraph.git
cd MealGraph
```

### 2. Set up environment

```bash
pip install -r requirements.txt
```

### 3. Run API

```bash
cd api
python main.py
```