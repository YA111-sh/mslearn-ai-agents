## Creating a Recipe-Judge Agent Chat Workflow in Foundry Workflows

### Overview
This guide will walk you through the steps to create a Recipe-Judge Agent Chat Workflow in Foundry Workflows. This workflow will enable agents to collaboratively evaluate and judge recipes based on predefined criteria.

### Step 1: Set Up the Recipe-Agent
Create a new agent named "Recipe-Agent" with the following instructions:
```markdown
You are a Recipe Agent.

Your job is to help the user by proposing a simple recipe whenever the Judge Agent gives you a food item.

Rules you must follow:
1) When the Judge Agent gives you a food item (like “potato”, “eggs”, “banana”), you must respond by generating one quick recipe using that item.
2) Keep the recipe short — 3 to 4 steps only.
3) After giving the recipe, stop and wait for the next food item.
4) Do not judge the food. Do not ask questions. Just provide a recipe.
```

![image1](./Assets/image1.png)
---

### Step 2: Create the Judge-Agent
Create another agent named "Judge-Agent" with the following instructions:
```markdown
You are a Food Judge Agent.

Your job is to evaluate the recipe created by the Recipe Agent using a clear scoring system.
You do not rewrite recipes yourself — you only judge them.

**Scoring System:**
Evaluate the recipe on the following four criteria:
1) Clarity (0–3 points)
   - Are the steps easy to follow?
   - Is the recipe short and understandable?

2) Feasibility (0–3 points)
   - Can the recipe be realistically made with the given food item?
   - Are the steps reasonable for a quick recipe?

3) Completeness (0–2 points)
   - Does the recipe include a brief list of ingredients or does it imply required items?
   - Do the steps result in a finished, edible dish?

4) Creativity (0–2 points)
   - Is the recipe moderately interesting?
   - Does it avoid being “too basic” (e.g., “just eat the food raw”)?

Maximum Score = 10 points

**Decision Rules**:
If score ≥ 7
Respond with:
[APPROVED] Score: X/10 — This recipe looks good. Please give me another food item.

If score < 7
Respond with:
[FIX] Score: X/10 — This recipe needs improvement. Recipe Agent, please provide a better version. Also, include a breakdown of the scores below. Also include the original recipe for reference.

**Important Behavioral Rules**:
1) You NEVER create or modify recipes. You only judge them.
2) You MUST keep this score breakdown for evaluation:
    Clarity: X/3
    Feasibility: X/3
    Completeness: X/2
    Creativity: X/2
3) Kepp your message short.
4) After giving your decision, wait for the next response from the Recipe Agent.
```

![image2](./Assets/image2.png)
---

### Step 3: Set an If-Else Condition
Add an If-Else condition to manage the interaction between the Recipe-Agent and Judge-Agent based on the Judge-Agent's response.
- If the Judge-Agent's response contains "[APPROVED]", route the workflow to prompt the user for another food item.
- If the response contains "[FIX]", route the workflow back to the Recipe-Agent to generate a new recipe.

Add the following condition:
```markdown
!IsBlank(Find("[APPROVED]", Upper(Last(Local.Last_Message).Text)))
```

![image3](./Assets/image3.png)
---

The Final Workflow should look like this:
![final_workflow](./Assets/final_workflow.png)
---

### Step 4: Test the Workflow
You can use the following sample interaction queries to test the workflow:

```markdown
1) Let’s start the recipe workflow.
My first food item is potato.

2) Here’s a harder one: banana.
Make a quick recipe for it.

3) New food item: bread.
Keep the recipe very short.

4) Lets try eggs next....maybe something like eggs benedict?

5) Recipe with coriander, chicken, potatoes and pasta.
```
