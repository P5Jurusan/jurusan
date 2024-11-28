// JavaScript untuk menampilkan pratinjau gambar
document.addEventListener('DOMContentLoaded', () => {
    const profilePicInput = document.getElementById('profile_pic');
    const preview = document.getElementById('preview');

    profilePicInput.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                preview.src = e.target.result;
                preview.style.display = 'block';
            };
            reader.readAsDataURL(file);
        } else {
            preview.style.display = 'none';
        }
    });
});
