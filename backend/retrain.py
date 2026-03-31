import json

print("Updating chatbot knowledge...")

with open("data/knowledge.json") as f:
    knowledge = json.load(f)

print("Knowledge loaded:", len(knowledge))