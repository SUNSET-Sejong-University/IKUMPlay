#include <stdio.h>
#include <string.h>
#include <ctype.h>

#define RESET   "\x1b[0m"
#define BLUE    "\x1b[36m"
#define GREEN   "\x1b[32m"
#define YELLOW  "\x1b[33m"
#define RED     "\x1b[31m"

#define PLAY    "▶"

const char *ASCII_ART =
"██╗██╗  ██╗██╗   ██╗███╗   ███╗\n"
"██║██║ ██╔╝██║   ██║████╗ ████║\n"
"██║█████╔╝ ██║   ██║██╔████╔██║\n"
"██║██╔═██╗ ██║   ██║██║╚██╔╝██║\n"
"██║██║  ██╗╚██████╔╝██║ ╚═╝ ██║\n"
"╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝\n";

void help() {
    printf(YELLOW "Commands: help, about, skills, projects, contact, exit\n" RESET);
}
void about() {
    printf(GREEN "Hi, I'm Ikum " PLAY "!\nPassionate about C and building fun terminal apps.\n" RESET);
}
void skills() {
    printf(GREEN "Skills: C, Python, Git, Linux\n" RESET);
}
void projects() {
    printf(GREEN "Projects: terminal-portfolio, small games, study tools\n" RESET);
}
void contact() {
    printf(GREEN "Email: you@example.com\nGitHub: https://github.com/yourname\n" RESET);
}

int main() {
    char cmd[50];

    printf(BLUE "%s" RESET, ASCII_ART);
    // ASCII-ийн доор ikum▶ мөр нэмсэн
    printf(GREEN "ikum" PLAY RESET "\n\n");

    printf("Type 'help' to see commands.\n\n");

    while (1) {
        // Prompt дээр ч мөн ikum▶ гарна
        printf(BLUE "ikum" PLAY "@portfolio$ " RESET);

        if (!fgets(cmd, sizeof(cmd), stdin)) break;

        cmd[strcspn(cmd, "\n")] = 0;
        for (int i = 0; cmd[i]; i++) cmd[i] = (char)tolower((unsigned char)cmd[i]);

        if (strcmp(cmd, "help") == 0) help();
        else if (strcmp(cmd, "about") == 0) about();
        else if (strcmp(cmd, "skills") == 0) skills();
        else if (strcmp(cmd, "projects") == 0) projects();
        else if (strcmp(cmd, "contact") == 0) contact();
        else if (strcmp(cmd, "exit") == 0) break;
        else if (strlen(cmd) == 0) continue;
        else printf(RED "Unknown command: %s\n" RESET, cmd);
    }

    printf("Goodbye!\n");
    return 0;
}
