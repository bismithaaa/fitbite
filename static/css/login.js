alert("js connected");
const signUpButton = document.getElementById('signUp');
const signInButton = document.getElementById('signIn');
const container = document.getElementById('container');

signUpButton.addEventListener('click', () => {
    container.classList.add("right-panel-active");
});

signInButton.addEventListener('click', () => {
    container.classList.remove("right-panel-active");
});

// Form validation and submission
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Get all inputs in the form
        const inputs = this.querySelectorAll('input');
        let isValid = true;
        
        // Simple validation
        inputs.forEach(input => {
            if (input.type !== 'checkbox' && !input.value.trim()) {
                isValid = false;
                input.style.borderColor = '#f44336';
            } else {
                input.style.borderColor = '#e0e0e0';
            }
            
            // Email validation
            if (input.type === 'email' && input.value.trim()) {
                const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailPattern.test(input.value.trim())) {
                    isValid = false;
                    input.style.borderColor = '#f44336';
                }
            }
            
            // Password confirmation validation
            if (input.placeholder === 'Confirm password' && input.value.trim()) {
                const password = this.querySelector('input[placeholder="Password"]').value;
                if (password !== input.value) {
                    isValid = false;
                    input.style.borderColor = '#f44336';
                    alert('Passwords do not match!');
                }
            }
        });
        
        // If valid, simulate form submission
        if (isValid) {
            const btn = this.querySelector('button');
            const originalText = btn.innerHTML;
            
            // Show loading state
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            btn.disabled = true;
            
            // Simulate API call
            setTimeout(() => {
                alert('Form submitted successfully! In a real application, this would connect to a backend.');
                btn.innerHTML = originalText;
                btn.disabled = false;
                
                // Reset form
                this.reset();
            }, 1500);
        }
    });
});

// Add focus effects to inputs
document.querySelectorAll('input').forEach(input => {
    input.addEventListener('focus', function() {
        this.parentElement.querySelector('i').style.color = '#2E7D32';
    });
    
    input.addEventListener('blur', function() {
        this.parentElement.querySelector('i').style.color = '#4CAF50';
    });
});