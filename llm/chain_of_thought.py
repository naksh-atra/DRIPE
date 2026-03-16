class PromptBuilder:
    @staticmethod
    def build_cot_prompt(drug: str, disease: str, paths: list, literature: list, safety: dict) -> str:
        system_msg = (
            "You are a biomedical research assistant. Your role is to explain why a drug may be a candidate "
            "for repurposing based on provided graph paths and literature evidence. You must cite every claim "
            "with a specific source. You must never use language that implies clinical recommendation, "
            "dosage, or direct patient application. You must never fabricate citations. If a claim cannot be "
            "supported by the provided context, you must say so explicitly."
        )
        
        user_content = f"Target Drug: {drug}\nTarget Disease: {disease}\n\n"
        user_content += "Graph Evidence:\n"
        for i, path in enumerate(paths):
            user_content += f"{i+1}. {path}\n"
            
        user_content += "\nLiterature Evidence:\n"
        for lit in literature:
            user_content += f"- {lit['text']} (PMID: {lit['pmid']})\n"
            
        user_content += f"\nSafety Profile (OpenFDA):\n{safety}\n\n"
        user_content += (
            "Task: Produce a Chain-of-Thought explanation (5-8 sentences) explaining the mechanism "
            "supporting this hypothesis. Add a citation at the end of every sentence."
        )
        
        return f"{system_msg}\n\n{user_content}"
