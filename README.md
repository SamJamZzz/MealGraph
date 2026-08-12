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

* FastAPI
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

Nutrition field semantics (column order, units, and known estimation limits) are documented in [`data-pipeline/NUTRITION_COLUMNS.md`](data-pipeline/NUTRITION_COLUMNS.md).

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

---

### 2. Set up Python environment

#### Create virtual environment

```bash
python3.11 -m venv .venv
```

#### Activate it

```bash
source .venv/bin/activate
```

#### Install dependencies

```bash
pip install -r requirements.txt
```

---

### 3. Verify setup

```bash
python -c "import pandas as pd; print(pd.__version__)"
```

---

### 4. Run the data pipeline

```bash
cd data-pipeline/scripts
python parse_recipes.py
```

This parses the raw Food.com dataset and writes a processed copy to `data-pipeline/processed/`.

---

*The API (`api/`) hasn't been implemented yet — data pipeline work is currently in progress. This section will be updated once `api/main.py` exists.*