import React, { useState, useEffect } from 'react';
import axios from 'axios';

const QuestionList = () => {
  const [questions, setQuestions] = useState([]);

  useEffect(() => {
    axios.get('/api/get_questions')
      .then(response => setQuestions(response.data))
      .catch(error => console.error('Error fetching questions:', error));
  }, []);

  return (
    <div className="question-list">
      <h2>Interview Questions</h2>
      <ul>
        {questions.map((question) => (
          <li key={question.id}>{question.question}</li>
        ))}
      </ul>
    </div>
  );
};

export default QuestionList;
