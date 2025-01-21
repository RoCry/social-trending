> all the docs in this folder are for the llm

# Tech
```mermaid
graph TD
    subgraph GitHub-Action
        subgraph Sources
            A1[Reddit]
            A2[Hacker News]
            A3[Twitter]
            A1 & A2 & A3 --> A[Crawler]
        end

        A --> |Item| B[Transformer]
    
        subgraph Processing
            B --> C[AI Enhancement]
            C --> |Add Summary| C1[Content Summary]
            C --> |Add Insights| C3[Comment Analysis]
        end
        
        subgraph Export
            C1 & C3 --> H[Exporter]
            H --> |Static File| I[JSON File]
            H --> |RSS Compatible| J[JSON Feed]
            H --> |Static Site| K[HTML]
        end
    end

    subgraph Consumers
        I --> |API| L[3rd Party Clients]
        J --> |Feed| M[RSS Readers]
        K --> |Website| X[GitHub Pages]
    end
```
