# Income Analyzer V16 Model 
This repo houses the Commerical Income Products Income Analyzer Model V16. It takes bank transaction data for individuals and predicts their income health based off the data.

# Getting Started

1.	Clone this respository (`git clone https://dmaassociates@dev.azure.com/dmaassociates/Model%20Factory/_git/Income_Analyzer_V16`) to your local machine to begin development. 
2. We have up to 8 developers working on this project. Follow the PR process outlined below to contribute.
3. Software dependencies
	  - see `requirements.txt`
    - You should use a virtual environment for this project. Run `python -m venv venv` if you haven't created one.
    - Run `pip install -r requirements.txt` to install all the package dependencies.
3. Configure Linter for VSCode
    - Automatic linting on save is configured for this project if you are using VSCode as your IDE and have `ruff` installed
    - If you don't have `ruff` installed, you can install the VSCode Extension [here](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff)
    - Ruff is a comprehensive, fast, industry-leading Python linter to enforce code style, code quality and readability

# Release Process

We are currently maintaining a separate repository for deployments to the Dev environment and above. It is essentially a copy of this repo. We will streamline this process eventually as this is highly-prone to bugs, but is the process nonetheless.

When deploying to Dev (CIP Project) you should follow these steps:

1. Ensure the `CHANGELOG.md` and `version.txt` files are up to date.
2. Cut a release to the Test Bed server by navigating to Pipelines > Releases > [Income_Analyzer_V16](https://dev.azure.com/dmaassociates/Model%20Factory/_release?_a=releases&view=mine&definitionId=11).
3. Click "Create Release", select the version of the model you want to release, and then click "Create".
4. Log into the `MDLTESTBED01` server, and you will be able to run a test utility to run the smoke tests for the model.
5. On `MDLTESTBED01`: navigate to where `/test_scripts` is and choose a test utility you want to run.
6. On `MDLTESTBED01`: Right-click on the test utility you want to run and click "Run with Powershell".
7. On `MDLTESTBED01`: Wait for the terminal to close, then you can navigate to the `/Logs` directory to see the output of the model runs.
8. On `MDLTESTBED01`: If any errors are present, raise them in `#ia-model-engineering` Slack channel and do not continue the release process unless there is a sign-off.
9. If no errors are present, the model is considered ready to promote to Dev.
10. To promote to Dev, the code from Model Factory must be merged into the [CIP_PYEngine_Code repo](https://dev.azure.com/dmaassociates/CIP_IPM_Chirp/_git/CIP_IPM_PYEngineCode).
11. To get the code change, copy-paste the `/src` and `/test` directories from this project in a branch for the CIP project. If there are changes to other files that need updating, copy-paste them as well. **Be sure not to include unnecessary changes to files, for example in `azure-pipelines.yaml` files**.
12. Make a PR with the code changes and updated `CHANGELOG.md` file and ensure the version is bumped. The PR title should indicate the version update, refer to a promotion PR as example. **Double check the PR does not include unwanted changes, this is common when copy-pasting**.
13. Once the PR is made, passes the build validation, and receives approval, hit Merge (make sure Squash Commit).
14. The merge will trigger the release pipeline which will build and push the code to the Dev server. The promotion to Dev is now complete, and higher environments require special approval from key stakeholders.

# Making Pull Requests

- Any notable code change to this project must include a change to the `CHANGELOG.md` file in its accompanying PR.
- The `version.txt` file must also be bumped according to [SemVer](https://semver.org/) guidelines.
- When creating a PR, test and lint pipelines will run to ensure the PR is not inadvertently breaking the model. If you are changing behavior and expect a test to break as a result, update the test to reflect the new desired behavior. 

### Terminal (recommended for larger changes)

Creating a PR through the terminal is easy with knowledge of git. If you are new to git, once you get the hang of the few relevant commands it will be a very straightforward process to create PRs. The steps are as follows:

- After cloning the repo, open a terminal window and navigate (`cd`) to the root of the project directory
- Create a new branch: `git checkout -b <your-branch-name>`
- Make your code edits in the editor of your choice (VSCode, Spyder, etc.)
- Once you are ready to commit your changes, stage them: `git add .`
- Commit your changes with a commit message: `git commit -m "<your-commit-message>"`
- Now you have committed your changes on your local branch, it's time to push the branch to the remote origin (Azure): `git push origin <your-branch-name>`
- Navigate to Azure and click on the button that says "Create a Pull Request" for the branch you just pushed
- Write a description and title and create the PR
- This will trigger the build and test pipeline to run automatically. If it passes, you will be able to merge to master!
  - Leave the setting enabled to delete source branch after merge

- When you want to make changes again, switch back to the master branch (`git checkout master`) and *make sure to pull the latest changes from the remote repository*: `git pull origin master`. If it gives you an error try `git rebase origin/master`.
- Now you are ready the repeat the process above for your changes

### Azure UI (recommended for smaller changes)

When using the Azure UI you won't use git. You can simply create a branch through the UI and edit the files within the UI. This is easy enough for small changes, but becomes difficult to manage for larger changes since you are not using a real code editor like VS Code or Spyder. The steps are as follows:

- At the top of the main screen, click on the dropdown with "master" -> "+ New Branch"
- A modal will open up where you give your branch a name and then hit Create
- The UI will automatically update to be on the new branch, so you can now navigate through the files and edit them through the UI
- Once you are done editing and making your commits, on the left panel under "Repos" click "Pull Requests"
- Create a new Pull Request, it should automatically default to select your new branch as the source branch and master as the destination branch (if not, just select them)
- Now you can write a title and description for the PR and create one. 
- This will trigger the build and test pipeline to run automatically. If it passes, you will be able to merge to master!
  - Leave the setting enabled to delete source branch after merge



