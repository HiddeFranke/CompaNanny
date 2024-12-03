# CompaNanny
Inspectierapport Analyser




import subprocess

def push_to_github(file_path, commit_message="Update dataset"):
    """
    Push het bestand naar GitHub.
    Parameters:
    - file_path: Het pad naar het bestand dat je wilt pushen.
    - commit_message: De commitboodschap voor de wijziging.
    """
    try:
        # Voeg het bestand toe aan de staging area
        subprocess.run(["git", "add", file_path], check=True)
        # Commit de wijziging
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        # Push naar de remote repository
        subprocess.run(["git", "push"], check=True)
        st.success(f"Bestand succesvol naar GitHub gepusht: {file_path}")
    except subprocess.CalledProcessError as e:
        st.error(f"Fout bij het pushen naar GitHub: {e}")

data.to_excel("CompaNanny_Database.xlsx", index=False)
push_to_github("CompaNanny_Database.xlsx", commit_message="Nieuwe data toegevoegd na analyse")




save_file(current_prompt, "prompt_oud.txt")
save_file(new_prompt, "prompt.txt")
push_to_github(["prompt_oud.txt", "prompt.txt"], commit_message="Bijgewerkte prompts")



save_file("\n".join(updated_labels), "labels.txt")
push_to_github(["labels.txt"], commit_message="Bijgewerkte labels")
