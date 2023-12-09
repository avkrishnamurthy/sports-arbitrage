function valueToColor(value) {
    const maxVal = 25;
    const intensity = value / maxVal;
    const greyValue = 40;
    const greenValue = Math.round(255 * intensity);

    return `rgba(${greyValue},${greenValue},${greyValue})`;
}

// Function to update colors
function updateColors() {
    const elements = document.getElementsByClassName('value');
    for (let i = 0; i < elements.length; i++) {
        const value = parseInt(elements[i].innerText, 10);
        elements[i].style.color = valueToColor(value);
    }
}

// Call updateColors when the document loads
window.onload = updateColors;