#!/usr/bin/env python3
from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import Lambda
from diagrams.aws.integration import StepFunctions
from diagrams.aws.network import APIGatewayEndpoint
from diagrams.aws.ml import Bedrock
from diagrams.aws.security import SecretsManager
from diagrams.aws.database import RDS
from diagrams.generic.device import Mobile

# Configuração do diagrama
graph_attr = {
    "fontsize": "24",
    "bgcolor": "transparent",
    "pad": "0.5"
}

# Criar o diagrama
with Diagram(
    "Arquitetura do Gerador de Histórias",
    show=True,  
    direction="LR",
    filename="architecture-diagram",
    outformat="png"
):
    # Usuário
    user = Mobile("Usuário")
    
    # Serviços AWS em seu próprio grupo
    with Cluster("AWS"):
        # API Gateway e primeira Lambda
        api = APIGatewayEndpoint("API Gateway")
        api_lambda = Lambda("API\nHandler")
        
        # Step Functions e outras Lambdas
        with Cluster("Step Functions"):
            step_fn = StepFunctions("State Machine")
            
            with Cluster("Lambdas"):
                context = Lambda("Buscar\nContexto")
                story = Lambda("Gerar\nHistória")
        
        # Serviços AWS
        secrets = SecretsManager("Secrets\nManager")
        bedrock = Bedrock("Amazon\nBedrock")
    
    # Serviço Externo
    with Cluster("Serviço Externo"):
        pinecone = RDS("Pinecone")
    
    # Fluxo principal
    user >> Edge(color="darkgreen", label="1") >> api
    api >> Edge(color="darkgreen", label="2") >> api_lambda
    api_lambda >> Edge(color="darkgreen", label="3") >> step_fn
    
    # Fluxo do Step Functions
    step_fn >> Edge(color="blue", label="4") >> context
    step_fn >> Edge(color="orange", label="5") >> story
    story >> Edge(color="darkgreen", label="6") >> user
    
    # Conexões com serviços externos
    context >> Edge(color="blue", style="dashed", label="4.1") >> secrets
    context >> Edge(color="blue", style="dashed", label="4.2") >> pinecone
    story >> Edge(color="orange", style="dashed", label="5.1") >> bedrock
