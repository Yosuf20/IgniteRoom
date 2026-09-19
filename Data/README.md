# Mini Company Brain Dataset

Synthetic company data for a 20-person software company. All people, tickets, documents,
meetings, and messages are fictional and created for a hackathon demo.

## Data types
- 20 employee records
- 10 engineering/product tickets
- 5 meeting notes
- 3 PDF documents
- 3 Word documents
- 1 Excel company metrics workbook
- 3 free-text Slack/WhatsApp-style chat exports

## Suggested multi-hop questions
1. What caused the payment timeout, who handled it, and what migration decision followed?
2. Which meeting decision is connected to PAY-142 and PAY-151?
3. Who owns the PostgreSQL migration and which documents describe the affected system?
4. What relationship exists between DATA-31, DATA-44, and SEC-12?
5. What search problem was discussed in Slack, which ticket tracks it, and who owns the investigation?
6. Which employees are connected to the Payment Service incident through meetings, tickets, and chat?
7. What company decisions have both a meeting record and a corresponding ticket?

## Important
The dataset is intentionally small but cross-linked. The same employee names, services,
ticket IDs, and decisions appear across multiple sources so a knowledge layer can demonstrate
multi-hop retrieval and synthesis.
