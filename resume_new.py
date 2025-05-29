import streamlit as st
from PyPDF2 import PdfReader
import pandas as pd
from pdf2image import convert_from_bytes
import pytesseract
import io
import tempfile
import base64
from PIL import Image
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Function to extract text from PDF
def extract_text_from_pdf(file):
    file_bytes = file.read()
    filename = file.name.lower()
    text = ""

    try:
        # Try PDF text extraction
        if filename.endswith(".pdf"):
            pdf = PdfReader(io.BytesIO(file_bytes))
            text = "".join(page.extract_text() or "" for page in pdf.pages).strip()

        # If text is empty, or if file is an image, use OCR
        if not text:
            if filename.endswith(".pdf"):
                images = convert_from_bytes(file_bytes)
            else:
                images = [Image.open(io.BytesIO(file_bytes))]

            text = "\n".join(pytesseract.image_to_string(img) for img in images).strip()

    except Exception as e:
        print(f"Text extraction failed for {filename}: {e}")

    return text

	
# Function to rank resumes based on job description
def rank_resumes(job_description, resumes):
    #Combine JD with resumes
    documents = [job_description] + resumes
    documents = [doc.strip() for doc in documents if doc.strip()]
    #if len(documents) <= 1:
        #raise ValueError("No valid resumes were found. Please upload the resumes.")
    vectorizer = TfidfVectorizer().fit_transform(documents)
    vectors = vectorizer.toarray()

    # Calculate cosine similarity
    job_description_vector = vectors[0]
    resume_vectors = vectors [1:]
    cosine_similarities = cosine_similarity([job_description_vector], resume_vectors).flatten()
    return cosine_similarities
    
def afterSubmit():        
    if uploaded_files and job_description:
        st.header("Ranking resumes...")

    resumes = []
    valid_filenames = []
    for file in uploaded_files:
        text = extract_text_from_pdf(file) #Fn calling
        if text.strip():
            resumes.append(text)
            valid_filenames.append(file.name)
        print(f"{file.name}: {len(text)} characters extracted.")

    try:
        # Ranking of resumes
        scores = rank_resumes(job_description, resumes)

        # Showing scores of resumes
        results = pd.DataFrame({"Resume": valid_filenames, "Score": scores})
        results = results.sort_values(by="Score",ascending=False)
        results["Rank"]=range(1,len(results)+1)
        results=results[["Rank","Resume","Score"]]
        st.session_state.results = results

        st.dataframe(results, hide_index=True)

    except ValueError as e:
        st.error(f"Error: {e}")
    st.success("Ranking Complete!")
    st.session_state.resume_files = {file.name: file for file in uploaded_files}
        
# Streamlit app
st.title("AI Powered Resume Screening and Candidate Ranking System")
# Initialize session state variable
if "resume_files" not in st.session_state:
    st.session_state.resume_files = {}
if "results" not in st.session_state:
    st.session_state.results = None
# I/P of Jd
st.header("Job Description")
job_description = st.text_area("Enter the job description")
# Block to upload the file (Resume)
st.header("Upload your Resumes in PDF, JPG or PNG Format")
uploaded_files = st.file_uploader("Upload PDF, JPG or PNG Files ",type=["pdf","png","jpg"], accept_multiple_files = True)

submit_disabledDocs = not(job_description.strip() and uploaded_files)
if st.button("Submit", disabled = submit_disabledDocs):
    afterSubmit()
if submit_disabledDocs:
    st.warning("Job description or Resume(s) was not uploaded")

if st.session_state.resume_files:
    st.markdown("### 🔍 Search and View Resume")

    resume_names = list(st.session_state.resume_files.keys())
    selected_resume = st.selectbox("Search resume by name", [""] + resume_names)

    if selected_resume:
        resume_file = st.session_state.resume_files[selected_resume]
        resume_file.seek(0)
        file_bytes = resume_file.read()

        # Display PDF or image
        if selected_resume.lower().endswith(".pdf"):
            try:
                base64_pdf = base64.b64encode(file_bytes).decode("utf-8")
                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Could not render PDF: {e}")
        else:
            try:
                image = Image.open(io.BytesIO(file_bytes))
                st.image(image, caption=selected_resume, use_container_width=True)
                
            except Exception as e:
                st.error(f"Could not display image: {e}")
                
st.markdown("### Download Resumes by Rank")

if st.session_state.results is not None:
    ranked_resumes_df = st.session_state.results

    # 🔍 Search bar for filtering resumes by name
    filtered_names = st.multiselect(
        "Search resume(s) by name",
        options=ranked_resumes_df["Resume"].tolist(),
        #default=ranked_resumes_df["Resume"].tolist()
    )

    # Filter results based on selected names
    filtered_results = ranked_resumes_df[ranked_resumes_df["Resume"].isin(filtered_names)]

    # Display download buttons for filtered results
    for index, row in filtered_results.iterrows():
        resume_file = next((f for f in uploaded_files if f.name == row["Resume"]), None)
        if resume_file:
            resume_file.seek(0)
            mime = (
                "application/pdf" if resume_file.name.lower().endswith(".pdf")
                else "image/jpeg" if resume_file.name.lower().endswith((".jpg", ".jpeg"))
                else "image/png"
            )
            st.download_button(
                label=f" Download Resume (Rank {row['Rank']}) - {row['Resume']}",
                data=resume_file.read(),
                file_name=resume_file.name,
                mime=mime
            )
            
st.markdown("""
    <style>
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: #f0f2f6;
        padding: 10px;
        text-align: center;
        font-size: 14px;
        color: gray;
    }
    </style>

    <div class="footer">
       A project by team OptiRecruit
    </div>
""", unsafe_allow_html=True)
