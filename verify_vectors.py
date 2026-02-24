import streamlit as st
from supabase_client import supabase

def verify_vectors():
    st.title("🔍 Vector Storage Verification")
    
    if supabase is None:
        st.error("❌ Supabase client is not initialized. Please check your secrets.")
        return

    try:
        # 1. Check table structure (via a sample query)
        st.write("### 📊 Database Summary")
        
        # Count total candidates
        count_res = supabase.table("shortlisted_candidates").select("id", count="exact").execute()
        total_candidates = count_res.count if hasattr(count_res, "count") else len(count_res.data)
        
        # Count candidates with embeddings
        emb_res = supabase.table("shortlisted_candidates").select("id").not_ .is_("embedding", "null").execute()
        candidates_with_vectors = len(emb_res.data)
        
        col1, col2 = st.columns(2)
        col1.metric("Total Candidates", total_candidates)
        col2.metric("Candidates with Vectors", candidates_with_vectors)
        
        if candidates_with_vectors == 0:
            st.warning("⚠️ No vectors found in the database. Ensure you have processed resumes and the threshold was met.")
        else:
            st.success(f"✅ Found {candidates_with_vectors} vectors stored successfully.")
            
        # 2. Show sample metadata
        st.write("### 🔬 Sample Vector Data")
        sample_res = supabase.table("shortlisted_candidates") \
            .select("candidate_name, final_score, embedding") \
            .not_.is_("embedding", "null") \
            .limit(3) \
            .execute()
            
        if sample_res.data:
            for i, row in enumerate(sample_res.data):
                with st.expander(f"Record {i+1}: {row['candidate_name']}"):
                    st.write(f"**Score:** {row['final_score']}")
                    # Show first 5 dimensions of the vector
                    emb = row['embedding']
                    if isinstance(emb, str):
                        # Handle potential string format if returning as text
                        dims = len(emb.split(','))
                        st.write(f"**Vector Dimensions:** {dims}")
                        st.code(f"{emb[:100]}...", language="text")
                    elif isinstance(emb, list):
                        st.write(f"**Vector Dimensions:** {len(emb)}")
                        st.code(f"{str(emb[:5])[:-1]}...]", language="python")
        
    except Exception as e:
        st.error(f"❌ Verification failed: {str(e)}")
        st.info("Tip: Ensure your Supabase schema matches the setup SQL (specifically the 'embedding' column in 'shortlisted_candidates').")

if __name__ == "__main__":
    # If running as a standalone streamlit app
    verify_vectors()
