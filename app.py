from flask import Flask, request, render_template, jsonify
import os
import subprocess
import traceback
from utils.faiss_utils import store_results_to_faiss, query_faiss
from utils.response_generator import generate_response
from agents.query_analysis import analyze_query_with_mistral

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"}), 200

@app.route("/recommend", methods=["POST"])
def process_query():
    try:
        user_query = request.form.get("user_query", "").strip()
        print(f"Received query: {user_query}")

        # Step 1: Analyze query
        analysis = analyze_query_with_mistral(user_query)
        print(analysis, "********")

        # Step 2: Run first.py if keywords exist
        if analysis.get("keywords"):
            print(f"Running first.py with keywords: {analysis['keywords']}")
            subprocess.run(
                ["python", "scripts/first.py", *analysis["keywords"]],
                check=False,
                timeout=600
            )

        # Step 3: Run second.py if job details exist
        if any([analysis.get("job_family"), analysis.get("job_level"), analysis.get("industry"), analysis.get("language")]):
            print("Running second.py with job details...")
            second_args = ["python", "scripts/second.py"]

            if analysis.get("job_family"):
                second_args += ["--job_family", analysis["job_family"][0]]
            if analysis.get("job_level"):
                second_args += ["--job_level", analysis["job_level"][0]]
            if analysis.get("industry"):
                second_args += ["--industry", analysis["industry"][0]]
            if analysis.get("language"):
                second_args += ["--language", analysis["language"][0]]

            subprocess.run(second_args, check=True)

            # Step 4: Run third.py if category exists
            if analysis.get("job_category"):
                print("Running third.py with category...")
                subprocess.run([
                    "python", "scripts/third.py",
                    "--job_category", analysis["job_category"][0]
                ], check=True)

        # Step 5: Store in FAISS
        print("Storing results to FAISS...")
        store_results_to_faiss()

        # Step 6: Query FAISS
        print("Querying FAISS...")
        results = query_faiss(user_query)
        print(f"FAISS Results: {results}")

        # Step 7: Generate response
        print("Generating final response...")
        response = generate_response(user_query, results)
        print("Response generated.")

        return jsonify({"success": True, "response": response})

    except Exception as e:
        print(f"Error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"success": False, "response": f"Error: {str(e)}"})

@app.route("/api/recommend", methods=["POST"])
def api_recommend():
    try:
        data = request.get_json()
        user_query = data.get("query", "").strip()

        if not user_query:
            return jsonify({"success": False, "error": "Query is required"}), 400

        print(f"API received query: {user_query}")

        # Step 1: Analyze query
        analysis = analyze_query_with_mistral(user_query)
        print(analysis, "<<< API Analysis")

        # Step 2: Run first.py if keywords exist
        if analysis.get("keywords"):
            subprocess.run(
                ["python", "scripts/first.py", *analysis["keywords"]],
                check=False,
                timeout=600
            )

        # Step 3: Run second.py if job details exist
        if any([analysis.get("job_family"), analysis.get("job_level"), analysis.get("industry"), analysis.get("language")]):
            second_args = ["python", "scripts/second.py"]
            if analysis.get("job_family"):
                second_args += ["--job_family", analysis["job_family"][0]]
            if analysis.get("job_level"):
                second_args += ["--job_level", analysis["job_level"][0]]
            if analysis.get("industry"):
                second_args += ["--industry", analysis["industry"][0]]
            if analysis.get("language"):
                second_args += ["--language", analysis["language"][0]]

            subprocess.run(second_args, check=True)

        # Step 4: Run third.py if job category exists
        if analysis.get("job_category"):
            subprocess.run([
                "python", "scripts/third.py",
                "--job_category", analysis["job_category"][0]
            ], check=True)

        # Step 5: Store to FAISS
        store_results_to_faiss()

        # Step 6: Query FAISS
        results = query_faiss(user_query)

        # Step 7: Format JSON output
        formatted = []
        for r in results:
            formatted.append({
                "assessment_name": r[0] or "nil",
                "link": r[1] or "nil",
                "remote_testing": r[2] or "nil",
                "adaptive_irt": r[3] or "nil",
                "test_type": r[4] or "nil",
                "duration": r[5] or "nil",
                "description": r[6] or "nil"
            })

        return jsonify({"success": True, "results": formatted}), 200

    except Exception as e:
        print("❌ API Error:", e)
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

