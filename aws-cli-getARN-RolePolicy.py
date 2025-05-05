import csv
import subprocess
import json

def backup_iam_policies(csv_file):
    """
    Reads IAM policy names from a CSV, retrieves their ARNs,
    and backs up the policy definitions to JSON files using get-policy-version,
    and updates the CSV.
    """
    with open(csv_file, 'r', newline='') as infile, \
         open('temp.csv', 'w', newline='') as outfile:

        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames + ['Role ARN', 'Policy File Name']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            policy_name = row['Role Name']
            print(f"Processing policy: {policy_name}")

            # 1. Retrieve Policy ARN
            policy_arn = get_policy_arn(policy_name)
            if not policy_arn:
                print(f"Warning: Could not find ARN for policy '{policy_name}'. Skipping.")
                row['Role ARN'] = 'NOT_FOUND'
                row['Policy File Name'] = 'N/A'
                writer.writerow(row)
                continue

            row['Role ARN'] = policy_arn

            # 2. Backup Policy to JSON (using get-policy-version)
            backup_file = f"Backup_{policy_name}.json"
            try:
                # Get default version ID
                cmd_get_policy = ['aws', 'iam', 'get-policy', '--policy-arn', policy_arn, '--output', 'json']
                result_get_policy = subprocess.run(cmd_get_policy, capture_output=True, text=True, check=True)
                policy_data = json.loads(result_get_policy.stdout)
                version_id = policy_data['Policy']['DefaultVersionId']

                # Get policy version
                cmd = ['aws', 'iam', 'get-policy-version',
                       '--policy-arn', policy_arn,
                       '--version-id', version_id,
                       '--output', 'json']

                result = subprocess.run(cmd, capture_output=True, text=True, check=True)

                # Parse JSON output
                policy_version_data = json.loads(result.stdout)

                # Write JSON to file with indentation
                with open(backup_file, 'w') as f:
                    json.dump(policy_version_data, f, indent=4)

                print(f"Policy '{policy_name}' backed up to '{backup_file}'")
                row['Policy File Name'] = backup_file

            except subprocess.CalledProcessError as e:
                print(f"Error backing up policy '{policy_name}': {e}")
                print(e.stderr)
                row['Policy File Name'] = 'ERROR'
            except KeyError as e:
                print(f"KeyError: {e}.  Problem parsing policy data for '{policy_name}'.")
                row['Policy File Name'] = 'ERROR'

            writer.writerow(row)

    # Replace the original file with the temp file
    import os
    os.replace('temp.csv', csv_file)


def get_policy_arn(policy_name):
    """
    Placeholder function to retrieve the Policy ARN based on the Policy Name.
    Replace this with your actual logic to fetch the ARN from AWS or your records.
    """
    # Example: Query AWS IAM to find the ARN
    try:
        cmd = ['aws', 'iam', 'list-policies', '--scope', 'Local', '--query', f'Policies[?PolicyName==`{policy_name}`].Arn', '--output', 'text']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        arn = result.stdout.strip()
        if arn:
            return arn
        else:
            return None
    except subprocess.CalledProcessError as e:
        print(f"Error retrieving policy ARN for '{policy_name}': {e}")
        return None


# Example usage
csv_file = r"C:\Users\JamieSmith\.vscode\cli\iam_roles-penTest-7.csv"
backup_iam_policies(csv_file)
