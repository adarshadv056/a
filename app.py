from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber
import pandas as pd
import io
from typing import Dict

app = FastAPI(title="FinSight Invoice Analyzer")

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze")
async def analyze_invoice(file: UploadFile = File(...)) -> Dict[str, float]:
    """
    Analyze PDF invoice and return sum of Total column for all Doodad rows.
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        # Read PDF content
        pdf_content = await file.read()
        
        # Extract table data using pdfplumber
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            doodad_total = 0.0
            
            for page in pdf.pages:
                # Extract tables from the page
                tables = page.extract_tables()
                
                for table in tables:
                    if not table:
                        continue
                    
                    # Convert table to DataFrame for easier processing
                    df = pd.DataFrame(table[1:], columns=table[0])  # Skip header row
                    
                    # Filter for Doodad rows and sum the Total column
                    if 'Product' in df.columns and 'Total' in df.columns:
                        doodad_rows = df[df['Product'].str.strip() == 'Doodad']
                        
                        for _, row in doodad_rows.iterrows():
                            try:
                                total_value = float(row['Total'])
                                doodad_total += total_value
                            except (ValueError, TypeError):
                                continue
        
        return {"sum": doodad_total}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@app.get("/")
async def root():
    return {"message": "FinSight Invoice Analyzer API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
