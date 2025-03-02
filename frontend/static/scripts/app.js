document.addEventListener("DOMContentLoaded", () => {
    const resumeForm = document.getElementById("resume-form");
    const resumeInput = document.getElementById("resume");
    const questionContainer = document.getElementById("questionContainer");
    const questionDisplay = document.getElementById("question-display");
    const loadingSpinner = document.getElementById("loading-spinner");

    let questions = [];
    let currentQuestionIndex = 0;
    let candidateGender = "male";

    resumeForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const file = resumeInput.files[0];
        if (!file) {
            alert("Please upload a resume.");
            return;
        }

        loadingSpinner.style.display = "block"; // Show loading

        const formData = new FormData();
        formData.append("resume", file);
        formData.append("csrfmiddlewaretoken", document.querySelector('[name=csrfmiddlewaretoken]').value);

        try {
            const response = await fetch("/upload-resume/", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                throw new Error(`Error: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            alert(`Welcome, ${data.name}!`);
            questions = data.questions;
            candidateGender = data.gender;
            currentQuestionIndex = 0;

            resumeForm.style.display = "none";
            questionDisplay.style.display = "flex";
            showQuestion();
        } catch (error) {
            console.error(error);
            alert("An error occurred while processing the resume.");
        } finally {
            loadingSpinner.style.display = "none"; // Hide loading
        }
    });

    function showQuestion() {
        if (currentQuestionIndex < questions.length) {
            questionContainer.textContent = questions[currentQuestionIndex];
            questionContainer.style.animation = "fadeInScale 1.5s ease-in-out";
            readAloud(questions[currentQuestionIndex]);
        } else {
            questionContainer.textContent = "Interview Completed. Thank you!";
        }
    }

    function readAloud(text) {
        if ("speechSynthesis" in window) {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = "en-US";
            utterance.rate = 1;
            utterance.pitch = 1;

            const voices = speechSynthesis.getVoices();
            let selectedVoice = voices.find(voice => 
                candidateGender === "female" ? voice.name.includes("Male") : voice.name.includes("Female")
            );

            if (!selectedVoice) {
                selectedVoice = voices[0]; // Fallback voice
            }
            utterance.voice = selectedVoice;

            utterance.onend = () => {
                startListening();
            };

            speechSynthesis.speak(utterance);
        } else {
            console.error("Text-to-Speech is not supported in this browser.");
            alert("Your browser does not support Text-to-Speech functionality.");
        }
    }

    function startListening() {
        if (!("webkitSpeechRecognition" in window)) {
            alert("Speech recognition is not supported in your browser.");
            return;
        }

        const recognition = new webkitSpeechRecognition();
        recognition.lang = "en-US";
        recognition.continuous = false;
        recognition.interimResults = false;

        questionContainer.textContent = "Listening... 🎤";

        recognition.onresult = async (event) => {
            const userResponse = event.results[0][0].transcript;
            console.log("User said:", userResponse);
            questionContainer.textContent = `You said: "${userResponse}"`;

            // Send response to backend for analysis
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
                console.log("Feedback:", feedback.message);
                alert(feedback.message);
            } catch (error) {
                console.error("Error sending response:", error);
            }

            setTimeout(() => {
                currentQuestionIndex++;
                showQuestion();
            }, 2000);
        };

        recognition.onerror = (event) => {
            console.error("Speech recognition error:", event.error);
            questionContainer.textContent = "Didn't catch that. Please try again.";
            setTimeout(() => {
                startListening(); // Retry once
            }, 2000);
        };

        recognition.start();
    }
    
    speechSynthesis.onvoiceschanged = () => {
        console.log("Voices loaded");
    };
});












// document.addEventListener("DOMContentLoaded", () => {
//     const resumeForm = document.getElementById("resume-form");
//     const resumeInput = document.getElementById("resume");
//     const questionContainer = document.getElementById("questionContainer");
//     const questionDisplay = document.getElementById("question-display");
//     const loadingSpinner = document.getElementById("loading-spinner");

//     let questions = [];
//     let currentQuestionIndex = 0;
//     let candidateGender = "male"; 

//     resumeForm.addEventListener("submit", async (e) => {
//         e.preventDefault();
//         const file = resumeInput.files[0];
//         if (!file) {
//             alert("Please upload a resume.");
//             return;
//         }
//         loadingSpinner.style.display = "block";

//         const formData = new FormData();
//         formData.append("resume", file);

//         const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
//         formData.append("csrfmiddlewaretoken", csrfToken);

//         try {
//             const response = await fetch("/upload-resume/", {
//                 method: "POST",
//                 body: formData,
//             });

//             if (!response.ok) {
//                 throw new Error(`Error: ${response.status} ${response.statusText}`);
//             }

//             const data = await response.json();
//             alert(`Welcome, ${data.name}!`);
//             questions = data.questions;
//             candidateGender = data.gender; 
//             currentQuestionIndex = 0;
//             resumeForm.style.display = "none";
//             questionDisplay.style.display = "flex";
//             showQuestion();
//         } catch (error) {
//             console.error(error);
//             alert("An error occurred while processing the resume.");
//         } finally {
//             loadingSpinner.style.display = "none";
//         }
//     });

//     function showQuestion() {
//         if (currentQuestionIndex < questions.length) {
//             questionContainer.textContent = questions[currentQuestionIndex];
//             questionContainer.style.animation = "fadeInScale 1.5s ease-in-out";
//             readAloud(questions[currentQuestionIndex]);
//         } else {
//             questionContainer.textContent = "All questions have been asked.";
//         }
//     }

//     function readAloud(text) {
//         if ("speechSynthesis" in window) {
//             const utterance = new SpeechSynthesisUtterance(text);
//             utterance.lang = "en-US";
//             utterance.rate = 1;
//             utterance.pitch = 1;

           
//             const voices = speechSynthesis.getVoices();
//             const femaleVoice = voices.find(voice => voice.name.includes("Female"));
//             const maleVoice = voices.find(voice => voice.name.includes("Male"));

//             if (candidateGender === "female" && maleVoice) {
//                 utterance.voice = maleVoice;
//             } else if (candidateGender === "male" && femaleVoice) {
//                 utterance.voice = femaleVoice;
//             }

//             utterance.onend = () => {
//                 currentQuestionIndex++;
//                 showQuestion();
//             };

//             speechSynthesis.speak(utterance);
//         } else {
//             console.error("Text-to-Speech is not supported in this browser.");
//             alert("Your browser does not support Text-to-Speech functionality.");
//         }
//     }
//     speechSynthesis.onvoiceschanged = () => {
//         console.log("Voices loaded");
//     };
// });