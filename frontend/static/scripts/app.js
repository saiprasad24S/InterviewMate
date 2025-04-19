document.addEventListener("DOMContentLoaded", function () {
    console.log("DOM fully loaded");

    const resumeForm = document.getElementById("resume-form");
    const uploadContainer = document.getElementById("upload-container");
    const questionDisplay = document.getElementById("question-display");
    const questionContainer = document.getElementById("questionContainer");
    const loadingSpinner = document.getElementById("loading-spinner");
    const timerDisplay = document.getElementById("timer-display");
    const feedbackDisplay = document.getElementById("feedback-display");
    const interviewDurationInput = document.getElementById("interview-duration");
    const languageInput = document.getElementById("language");

    let questions = [];
    let currentQuestionIndex = 0;
    let candidateGender = "male";
    let selectedLanguage = "English"; // Default language
    let feedbackCollection = [];
    let timerInterval = null;
    let interviewEnded = false;
    let interviewDuration;

    function startTimer() {
        let timeLeft = interviewDuration;
        timerInterval = setInterval(() => {
            timeLeft -= 1000;
            const minutes = Math.floor(timeLeft / 60000);
            const seconds = Math.floor((timeLeft % 60000) / 1000);
            timerDisplay.textContent = `Time Remaining: ${minutes}:${seconds < 10 ? '0' + seconds : seconds}`;
            if (timeLeft <= 0) {
                clearInterval(timerInterval);
                endInterview();
            }
        }, 1000);
        console.log("Timer started with duration:", interviewDuration, "ms");
    }

    async function endInterview() {
        console.log("Interview ended");
        interviewEnded = true;
        clearInterval(timerInterval);
        timerInterval = null;
        speechSynthesis.cancel();
        questionContainer.textContent = "Interview Completed. Calculating results...";
    
        try {
            const response = await fetch("/stop-eye-tracking/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
                },
            });
            const data = await response.json();
            console.log("Eye tracking stop response:", data);
    
            // Ensure overall score is displayed prominently out of 100
            const overallScore = data.overall_score.toFixed(2);
            questionContainer.innerHTML = `
                <h2>Interview Completed</h2>
                <p>Your Overall Score: <strong>${overallScore}/100</strong></p>
            `;
    
            // Display feedback without improvement suggestions
            if (feedbackCollection.length > 0) {
                const allFeedback = feedbackCollection.map((fb, index) => `
                    <div class="feedback-item">
                        <p><strong>Question ${index + 1}:</strong> ${fb.question}</p>
                        <p><strong>Your Answer:</strong> ${fb.answer}</p>
                        <p><strong>Feedback:</strong> ${fb.feedback}</p>
                    </div>
                `).join('<hr>');
                feedbackDisplay.innerHTML = `
                    <h3>Feedback</h3>
                    ${allFeedback}
                `;
                feedbackDisplay.style.display = "block";
            } else {
                feedbackDisplay.innerHTML = `
                    <h3>Feedback</h3>
                    <p>No feedback collected during the interview.</p>
                `;
                feedbackDisplay.style.display = "block";
            }
    
            // Visualization with Chart.js
            const attributes = data.attributes;
            const ctx = document.getElementById('performanceChart').getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Eye Contact', 'Nervousness', 'Confidence', 'Fluency', 'Intelligence'],
                    datasets: [{
                        label: 'Performance (%)',
                        data: [
                            attributes.eye_contact,
                            attributes.nervousness,
                            attributes.confidence,
                            attributes.fluency,
                            attributes.intelligence
                        ],
                        backgroundColor: ['#007bff', '#ff5733', '#28a745', '#ffca28', '#9c27b0'],
                        borderColor: ['#0056b3', '#e04e2b', '#218838', '#e0b400', '#7b1fa2'],
                        borderWidth: 1
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            title: { display: true, text: 'Percentage (%)' }
                        },
                        x: {
                            title: { display: true, text: 'Attributes' }
                        }
                    },
                    plugins: {
                        legend: { display: false },
                        title: { display: true, text: 'Interview Performance Metrics' }
                    }
                }
            });
            document.getElementById('performanceChart').style.display = 'block';
    
        } catch (error) {
            console.error("Error stopping eye tracking or rendering visualization:", error);
            questionContainer.innerHTML = `
                <h2>Interview Completed</h2>
                <p>Error calculating score. Please try again.</p>
            `;
            feedbackDisplay.innerHTML = `
                <h3>Feedback</h3>
                <p>Error occurred.</p>
            `;
            feedbackDisplay.style.display = "block";
        }
    }

    if (resumeForm) {
        resumeForm.addEventListener("submit", async function (e) {
            e.preventDefault();
            console.log("Form submitted");
            loadingSpinner.style.display = "block";

            const formData = new FormData(resumeForm);
            const durationMinutes = parseInt(interviewDurationInput.value, 10);
            selectedLanguage = languageInput.value.trim();
            if (isNaN(durationMinutes) || durationMinutes < 1) {
                alert("Please enter a valid duration (at least 1 minute).");
                loadingSpinner.style.display = "none";
                return;
            }
            if (!selectedLanguage) {
                alert("Please enter a valid language.");
                loadingSpinner.style.display = "none";
                return;
            }
            interviewDuration = durationMinutes * 60 * 1000;
            console.log("Interview Duration set to:", interviewDuration, "ms");
            console.log("Selected Language:", selectedLanguage);

            try {
                const response = await fetch("/upload-resume/", {
                    method: "POST",
                    body: formData,
                    headers: {
                        "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
                    },
                });

                const data = await response.json();
                console.log("Server response:", data);

                if (response.status === 200) {
                    questions = data.questions;
                    candidateGender = data.gender;
                    console.log("Questions received:", questions);
                    uploadContainer.style.display = "none";
                    questionDisplay.style.display = "flex";
                    console.log("Switched to question display");
                    interviewEnded = false;
                    currentQuestionIndex = 0;
                    feedbackCollection = [];
                    startTimer();
                    showQuestion();
                } else {
                    alert(data.error || "An error occurred while processing the resume.");
                }
            } catch (error) {
                console.error("Fetch error:", error);
                alert("An error occurred while processing the resume.");
            } finally {
                loadingSpinner.style.display = "none";
            }
        });
    }

    function showQuestion() {
        if (interviewEnded) {
            console.log("Interview has ended; no more questions.");
            return;
        }
        console.log("Showing question at index:", currentQuestionIndex, "Total questions:", questions.length);
        console.log("Timer active:", !!timerInterval);
        if (currentQuestionIndex < questions.length && timerInterval) {
            const questionText = questions[currentQuestionIndex].trim();
            console.log("Setting question text:", questionText);
            questionContainer.textContent = questionText;
            questionContainer.style.animation = "fadeInScale 1.5s ease-in-out";
            readAloud(questionText);
        } else {
            console.log("No more questions or timer ended; ending interview.");
            endInterview();
        }
    }

    function readAloud(text) {
        if (interviewEnded) {
            console.log("Interview has ended; no speech synthesis.");
            return;
        }
        console.log("Reading aloud question:", text);
        if ("speechSynthesis" in window) {
            const utterance = new SpeechSynthesisUtterance(text);
            const langCode = getLanguageCode(selectedLanguage);
            utterance.lang = langCode;
            utterance.rate = 1;
            utterance.pitch = 1;

            const voices = speechSynthesis.getVoices();
            if (voices.length === 0) {
                console.log("Voices not yet loaded; waiting...");
                speechSynthesis.onvoiceschanged = () => {
                    setVoice(utterance);
                    speechSynthesis.speak(utterance);
                };
            } else {
                setVoice(utterance);
                speechSynthesis.speak(utterance);
            }

            utterance.onend = () => {
                console.log("Speech ended; starting listening.");
                startListening();
            };
            utterance.onerror = (event) => {
                console.error("Speech synthesis error:", event.error);
                startListening();
            };
        } else {
            console.error("Text-to-Speech not supported.");
            alert("Your browser does not support Text-to-Speech.");
            startListening();
        }
    }

    function setVoice(utterance) {
        const voices = speechSynthesis.getVoices();
        const langCode = getLanguageCode(selectedLanguage);
        console.log("Available voices:", voices.map(v => `${v.name} (${v.lang})`));
        let selectedVoice;

        selectedVoice = voices.find(voice => 
            voice.lang === langCode && 
            (candidateGender === "female" ? voice.name.toLowerCase().includes("female") : voice.name.toLowerCase().includes("male"))
        ) || voices.find(voice => voice.lang === langCode);

        if (!selectedVoice) {
            selectedVoice = voices.find(voice => 
                voice.lang.startsWith(langCode.split('-')[0])
            );
        }
        if (!selectedVoice) {
            selectedVoice = voices[0];
            console.warn(`No voice for ${selectedLanguage} (${langCode}); using: ${selectedVoice.name} (${selectedVoice.lang})`);
        } else {
            console.log(`Selected voice: ${selectedVoice.name} (${selectedVoice.lang})`);
        }

        utterance.voice = selectedVoice;
    }

    function startListening() {
        if (interviewEnded) {
            console.log("Interview has ended; no more listening.");
            return;
        }
        console.log("Starting to listen for response to question", currentQuestionIndex + 1);
        if (!("webkitSpeechRecognition" in window)) {
            alert("Speech recognition not supported.");
            currentQuestionIndex++;
            setTimeout(showQuestion, 2000);
            return;
        }

        const recognition = new webkitSpeechRecognition();
        recognition.lang = getLanguageCode(selectedLanguage);
        recognition.continuous = false;
        recognition.interimResults = false;
        questionContainer.textContent = "Listening...";

        recognition.onresult = async (event) => {
            if (interviewEnded) {
                console.log("Interview ended during recognition; ignoring result.");
                return;
            }
            const userResponse = event.results[0][0].transcript;
            console.log("User said:", userResponse);
            questionContainer.textContent = `You said: "${userResponse}"`;

            try {
                const response = await fetch("/analyze-response/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
                    },
                    body: JSON.stringify({ question: questions[currentQuestionIndex], answer: userResponse }),
                });

                const feedback = await response.json();
                console.log("Feedback received:", feedback);
                feedbackCollection.push({
                    question: questions[currentQuestionIndex],
                    answer: userResponse,
                    feedback: feedback.feedback || "No feedback provided.",
                    improvement: feedback.improvement || "No improvement suggested."
                });
            } catch (error) {
                console.error("Error sending response:", error);
                feedbackCollection.push({
                    question: questions[currentQuestionIndex],
                    answer: userResponse,
                    feedback: "Error retrieving feedback",
                    improvement: "Check server connection."
                });
            }

            console.log("Incrementing question index from", currentQuestionIndex);
            currentQuestionIndex++;
            console.log("New question index:", currentQuestionIndex);
            setTimeout(() => {
                console.log("setTimeout triggered; showing next question.");
                showQuestion();
            }, 2000);
        };

        recognition.onerror = (event) => {
            if (interviewEnded) {
                console.log("Interview ended; ignoring recognition error.");
                return;
            }
            console.error("Speech recognition error:", event.error);
            questionContainer.textContent = "Didn't catch that. Please try again.";
            setTimeout(() => {
                console.log("Retrying listening after error.");
                startListening();
            }, 2000);
        };

        recognition.start();
    }

    function getLanguageCode(language) {
        const langMap = {
            "english": "en-US",
            "hindi": "hi-IN",
            "telugu": "te-IN",
            // Add more mappings as needed
        };
        return langMap[language.toLowerCase()] || "en-US"; // Default to en-US
    }

    speechSynthesis.onvoiceschanged = () => {
        console.log("Voices loaded");
    };
});

async function endInterview() {
    console.log("Interview ended");
    interviewEnded = true;
    clearInterval(timerInterval);
    timerInterval = null;
    speechSynthesis.cancel();
    questionContainer.textContent = "Interview Completed. Calculating results...";

    try {
        const response = await fetch("/stop-eye-tracking/", {
            method: "POST",
            headers: {
                "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
            },
        });
        const data = await response.json();
        console.log("Eye tracking stop response:", data);

        // Ensure overall score is displayed prominently out of 100
        const overallScore = data.overall_score.toFixed(2);
        questionContainer.innerHTML = `
            <h2>Interview Completed</h2>
            <p>Your Overall Score: <strong>${overallScore}/100</strong></p>
        `;

        // Display feedback and mandatory improvement suggestions
        if (feedbackCollection.length > 0) {
            const allFeedback = feedbackCollection.map((fb, index) => `
                <div class="feedback-item">
                    <p><strong>Question ${index + 1}:</strong> ${fb.question}</p>
                    <p><strong>Your Answer:</strong> ${fb.answer}</p>
                    <p><strong>Feedback:</strong> ${fb.feedback}</p>
                    <p><strong>Improvement Suggestion:</strong> ${fb.improvement}</p>
                </div>
            `).join('<hr>');
            feedbackDisplay.innerHTML = `
                <h3>Feedback and Improvement Suggestions</h3>
                ${allFeedback}
            `;
            feedbackDisplay.style.display = "block";
        } else {
            feedbackDisplay.innerHTML = `
                <h3>Feedback and Improvement Suggestions</h3>
                <p>No feedback collected during the interview.</p>
                <p><strong>Improvement Suggestion:</strong> You can tell it like this: Ensure you respond clearly and in detail to each question to showcase your skills effectively.</p>
            `;
            feedbackDisplay.style.display = "block";
        }

        // Visualization with Chart.js
        const attributes = data.attributes;
        const ctx = document.getElementById('performanceChart').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Eye Contact', 'Nervousness', 'Confidence', 'Fluency', 'Intelligence'],
                datasets: [{
                    label: 'Performance (%)',
                    data: [
                        attributes.eye_contact,
                        attributes.nervousness,
                        attributes.confidence,
                        attributes.fluency,
                        attributes.intelligence
                    ],
                    backgroundColor: ['#007bff', '#ff5733', '#28a745', '#ffca28', '#9c27b0'],
                    borderColor: ['#0056b3', '#e04e2b', '#218838', '#e0b400', '#7b1fa2'],
                    borderWidth: 1
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: { display: true, text: 'Percentage (%)' }
                    },
                    x: {
                        title: { display: true, text: 'Attributes' }
                    }
                },
                plugins: {
                    legend: { display: false },
                    title: { display: true, text: 'Interview Performance Metrics' }
                }
            }
        });
        document.getElementById('performanceChart').style.display = 'block';

    } catch (error) {
        console.error("Error stopping eye tracking or rendering visualization:", error);
        questionContainer.innerHTML = `
            <h2>Interview Completed</h2>
            <p>Error calculating score. Please try again.</p>
        `;
        feedbackDisplay.innerHTML = `
            <h3>Feedback and Improvement Suggestions</h3>
            <p>Error occurred.</p>
            <p><strong>Improvement Suggestion:</strong> You can tell it like this: Check your connection and ensure all responses are recorded properly next time.</p>
        `;
        feedbackDisplay.style.display = "block";
    }
}