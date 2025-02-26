const resumeForm = document.getElementById('resume-form');
const resumeInput = document.getElementById('resume');
const questionContainer = document.getElementById('questionContainer');
const questionDisplay = document.getElementById('question-display');

let questions = [];
let currentQuestionIndex = 0;

resumeForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const file = resumeInput.files[0];
    if (!file) {
        alert('Please upload a resume.');
        return;
    }

    const formData = new FormData();
    formData.append('resume', file);

    try {
        const response = await fetch('/upload-resume/', {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            throw new Error(`Error: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        alert(`Welcome, ${data.name}!`);
        questions = data.questions;
        currentQuestionIndex = 0;
        resumeForm.style.display = 'none'; // Hide the form
        questionDisplay.style.display = 'block'; // Show the question display section
        showQuestion();
    } catch (error) {
        console.error(error);
        alert('An error occurred while processing the resume.');
    }
});

function showQuestion() {
    if (currentQuestionIndex < questions.length) {
        questionContainer.textContent = questions[currentQuestionIndex];
        questionContainer.style.animation = 'fadeInScale 1.5s ease-in-out'; // Added animation
        readAloud(questions[currentQuestionIndex]);
    } else {
        questionContainer.textContent = 'All questions have been read.';
    }
}

function readAloud(text) {
    if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'en-US';
        utterance.rate = 1;
        utterance.pitch = 1;

        utterance.onend = () => {
            currentQuestionIndex++;
            showQuestion();
        };

        speechSynthesis.speak(utterance);
    } else {
        console.error('Text-to-Speech is not supported in this browser.');
        alert('Your browser does not support Text-to-Speech functionality.');
    }
}
















// const resumeForm = document.getElementById('resume-form');
// const resumeInput = document.getElementById('resume');

// resumeForm.addEventListener('submit', async (e) => {
//     e.preventDefault();

//     const file = resumeInput.files[0];
//     if (!file) {
//         alert('Please upload a resume.');
//         return;
//     }

//     const formData = new FormData();
//     formData.append('resume', file);

//     try {
//         const response = await fetch('/upload-resume/', {
//             method: 'POST',
//             body: formData,
//         });

//         if (!response.ok) {
//             throw new Error(`Error: ${response.status} ${response.statusText}`);
//         }

//         const data = await response.json();
//         alert(`Welcome, ${data.name}!`);
//         displayQuestions(data.questions);
//         hideForm();
//     } catch (error) {
//         console.error(error);
//         alert('An error occurred while processing the resume.');
//     }
// });

// function displayQuestions(questions) {
//     const instructionsSection = document.getElementById('instructions');
//     instructionsSection.innerHTML = ''; // Clear previous questions
//     const questionList = document.createElement('ul');

//     questions.forEach((question, index) => {
//         const listItem = document.createElement('li');
//         listItem.textContent = question;
//         questionList.appendChild(listItem);

//         // Trigger text-to-speech for each question
//         readAloud(`Question ${index + 1}: ${question}`);
//     });

//     instructionsSection.appendChild(questionList);
// }

// function readAloud(text) {
//     if ('speechSynthesis' in window) {
//         const utterance = new SpeechSynthesisUtterance(text);
//         utterance.lang = 'en-US';
//         utterance.rate = 1; // Adjust speed if necessary
//         utterance.pitch = 1; // Adjust pitch if necessary
//         speechSynthesis.speak(utterance);
//     } else {
//         console.error('Text-to-Speech is not supported in this browser.');
//         alert('Your browser does not support Text-to-Speech functionality.');
//     }
// }

// function hideForm() {
//     const formElement = document.getElementById('resume-form');
//     formElement.style.display = 'none';
// }

// // JavaScript for footer visibility on scroll
// let lastScrollY = window.scrollY;
// const footer = document.querySelector('footer');

// window.addEventListener('scroll', () => {
//     if (window.scrollY > lastScrollY) {
//         // Scrolling down
//         footer.classList.add('hidden-footer');
//     } else {
//         // Scrolling up
//         footer.classList.remove('hidden-footer');
//     }
//     lastScrollY = window.scrollY;
// });





