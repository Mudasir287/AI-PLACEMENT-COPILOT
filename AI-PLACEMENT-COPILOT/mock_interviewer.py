from typing import List, Dict, Any, Optional
from llm_client import LLMClient
from schemas import (
    InterviewQuestion,
    InterviewQuestionList,
    AnswerEvaluation
)


class MockInterviewer:
    """
    Targeted AI Interviewer Engine that dynamically formulates technical 
    questions on identified skill gaps and provides graded feedback.
    """

    def __init__(self):
        self.llm = LLMClient()

    def generate_questions(
        self,
        target_role: str,
        missing_skills: List[str],
        question_count: int = 3
    ) -> List[InterviewQuestion]:
        """
        Generates targeted technical interview questions focusing on candidate skill gaps.
        """
        skills_focus = ", ".join(missing_skills) if missing_skills else "Core Software Engineering & System Design"

        prompt = f"""
You are a Principal Technical Interviewer conducting a rigorous interview for a: {target_role}.

The candidate has identified skill gaps or requirements in: {skills_focus}.

Generate exactly {question_count} targeted technical interview questions specifically probing these areas.
For each question:
1. Specify which missing skill it assesses.
2. Set an appropriate difficulty level (Easy, Medium, Hard).
3. Formulate a realistic technical or system question.
4. Provide 3-4 bullet points of what a strong candidate's ideal answer must cover.
"""
        response_data: InterviewQuestionList = self.llm.generate_structured_output(
            prompt,
            InterviewQuestionList
        )
        return response_data.questions

    def evaluate_candidate_answer(
        self,
        question: str,
        targeted_skill: str,
        candidate_answer: str,
        ideal_points: Optional[List[str]] = None
    ) -> AnswerEvaluation:
        """
        Grades candidate response on a 1-10 scale and gives targeted feedback.
        """
        ideal_criteria = "\n".join([f"- {pt}" for pt in ideal_points]) if ideal_points else "General technical accuracy."

        prompt = f"""
You are a Senior Technical Hiring Manager evaluating a candidate's answer during a live interview.

Topic / Targeted Skill: {targeted_skill}
Interview Question: "{question}"
Key Expected Answer Points:
{ideal_criteria}

Candidate's Answer:
"{candidate_answer}"

Provide a structured evaluation:
1. Score the answer strictly between 1.0 and 10.0 based on technical depth and accuracy.
2. Highlight specific strengths in what they explained.
3. Call out crucial missing concepts or misconceptions.
4. Write a concise, high-impact exemplar response.
"""
        return self.llm.generate_structured_output(prompt, AnswerEvaluation)


# --- Day 9 Verification Pipeline ---
if __name__ == "__main__":
    interviewer = MockInterviewer()

    target_job = "Python AI Engineer"
    detected_missing_skills = ["Docker", "FastAPI", "Vector Embeddings"]

    print("\n🚀 GENERATING TARGETED INTERVIEW QUESTIONS...")
    print("=" * 60)

    questions = interviewer.generate_questions(
        target_role=target_job,
        missing_skills=detected_missing_skills,
        question_count=3
    )

    for q in questions:
        print(f"\n📌 Question #{q.question_id} [{q.difficulty.upper()}] - Topic: {q.targeted_skill}")
        print(f"❓ {q.question_text}")
        print("💡 Ideal Answer Key Points:")
        for pt in q.ideal_answer_points:
            print(f" • {pt}")

    # Test Answer Evaluation with a simulated candidate response
    test_question = questions[0]
    sample_candidate_answer = (
        "Docker creates containers that pack your code and dependencies together. "
        "It uses Dockerfile to build images, so your application works the same on every computer."
    )

    print("\n" + "=" * 60)
    print(f"🎙️ EVALUATING SAMPLE CANDIDATE ANSWER FOR TOPIC: {test_question.targeted_skill}")
    print(f"Candidate Answer: \"{sample_candidate_answer}\"")
    print("-" * 60)

    evaluation = interviewer.evaluate_candidate_answer(
        question=test_question.question_text,
        targeted_skill=test_question.targeted_skill,
        candidate_answer=sample_candidate_answer,
        ideal_points=test_question.ideal_answer_points
    )

    print(f"🎯 Score: {evaluation.score_out_of_10} / 10.0")
    print("\n✅ Strengths:")
    for s in evaluation.strengths:
        print(f" • {s}")
    print("\n⚠️ Missing Concepts:")
    for m in evaluation.missing_concepts:
        print(f" • {m}")
    print(f"\n✨ Exemplar Answer:\n{evaluation.improved_sample_answer}")
    print("=" * 60)
