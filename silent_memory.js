graph TD
    %% Styling
    classDef user fill:#f9f,stroke:#333,stroke-width:2px,color:black;
    classDef agent fill:#bbf,stroke:#333,stroke-width:2px,color:black;
    classDef memory fill:#bfb,stroke:#333,stroke-width:2px,color:black;
    classDef external fill:#fbb,stroke:#333,stroke-width:2px,color:black;
    classDef output fill:#ddd,stroke:#333,stroke-width:2px,color:black;

    %% Nodes
    User((User / UI)):::user
    
    subgraph Local_Environment ["Local Machine (LangGraph Orchestrator)"]
        direction TB
        InputProcessor[Input Processor<br/>(Client Name + History)]
        
        subgraph Memory_Layer ["Silent Memory Layer"]
            ChromaQuery[Query ChromaDB<br/>'Find Similar Verticals']:::memory
            ChromaStore[Store New Plays<br/>'Update Knowledge']:::memory
        end

        subgraph Agent_Workflow ["Agentic Workflow"]
            ContextMerger{Context Merger}
            CompScout[Competitor Scout<br/>(Search for Case Studies)]:::agent
            
            subgraph Id8_Loop ["Id8 Iteration Loop"]
                Generator[Divergent Generator<br/>(Create 10+ Ideas)]:::agent
                Refiner[Convergent Refiner<br/>(Filter to Top 3)]:::agent
            end
            
            AssetWriter[Asset Generator<br/>(Pellera Voice - Markdown)]:::agent
        end
    end

    subgraph External_Services ["External Services"]
        Gemini[Gemini Deep Research API<br/>(Base Prompt + Web Search)]:::external
    end

    Files(Markdown Output<br/>One-Pagers & Plans):::output

    %% Connections
    User --> InputProcessor
    InputProcessor --> Gemini
    InputProcessor --> ChromaQuery
    
    Gemini -- "Deep Client Report" --> ContextMerger
    ChromaQuery -- "Historical Sales Plays" --> ContextMerger
    InputProcessor -- "Past Sales History" --> ContextMerger
    
    ContextMerger --> CompScout
    CompScout -- "Competitor Proof Points" --> Generator
    
    Generator -- "Raw Ideas" --> Refiner
    Refiner -- "Critique & Select" --> Generator
    Refiner -- "Top 3 Plays" --> AssetWriter
    
    AssetWriter --> Files
    AssetWriter --> ChromaStore
    
    %% Feedback Loop
    ChromaStore -.-> ChromaQuery
