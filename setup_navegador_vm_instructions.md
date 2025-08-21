# Navegador VM Setup: Automated VS Code, Copilot, Codacy, and Git Integration

This guide explains the logic and steps behind the automated setup script for your Azure VM/container, enabling two fully independent VS Code sessions with Copilot, Codacy, and Git integration.

---

## Logic & Rationale
- **Isolation:** Two code-server instances run on different ports, each with its own user-data directory, ensuring independent VS Code environments and Copilot engines.
- **Parallel Development:** You can work in two browser tabs or windows, each with its own Copilot, Codacy, and GitLens extensions, avoiding interference.
- **Extension Management:** Extensions are installed in both sessions for consistent tooling.
- **Remote Options:** You can also use VS Code Remote - SSH for multiple native windows, each with its own Copilot session.

---

## Automated Actions in `setup_navegador_vm.sh`
1. **Conda Environment Activation:** Ensures all Python dependencies are installed in the correct environment.
2. **Pip Package Installation:** Installs all required Python packages for your project.
3. **code-server Installation:** Installs VS Code server if not already present.
4. **User Data Directories:** Creates `~/.vscode1` and `~/.vscode2` for isolated sessions.
5. **Start code-server Instances:** Launches two code-server servers on ports 8080 and 8081, each with its own config.
6. **Extension Installation:** Installs Copilot, Codacy, and GitLens in both sessions.
7. **Instructions Output:** Prints URLs and usage tips for both sessions and VS Code Remote - SSH.

---

## How to Use
1. **Run the Script Inside the Container:**
   ```bash
   bash setup_navegador_vm.sh
   ```
2. **Access VS Code Sessions:**
   - Open `http://<vm-ip>:8080` and `http://<vm-ip>:8081` in your browser.
   - Log in to Copilot with different accounts if you want true engine isolation.
3. **VS Code Remote - SSH:**
   - Open multiple VS Code windows on your local machine, each connected to the VM via SSH.
   - Each window can have its own workspace and Copilot session.
4. **Extension Management:**
   - Extensions are installed automatically, but you can add more via the VS Code UI.

---

## Troubleshooting & Tips
- If ports 8080/8081 are blocked, change them in the script and open them in your VM firewall.
- For more isolation, run code-server as different OS users.
- If Copilot sessions interfere, use separate GitHub accounts for each code-server instance.
- You can stop code-server instances with `pkill code-server` or by killing the process.

---

## References
- [code-server Docs](https://github.com/coder/code-server)
- [GitHub Copilot Extension](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot)
- [Codacy VS Code Extension](https://marketplace.visualstudio.com/items?itemName=codacy.codacy-vscode)
- [GitLens Extension](https://marketplace.visualstudio.com/items?itemName=eamodio.gitlens)
- [VS Code Remote - SSH](https://code.visualstudio.com/docs/remote/ssh)

---

This setup enables robust, parallel, and isolated development workflows on your Azure VM/container.
