from databricks.sdk import WorkspaceClient
from databricks.sdk.service import jobs

"""
In order to execute this program, you will need to set up databricks CLI profile
https://docs.databricks.com/en/dev-tools/cli/tutorial.html

The authentication can be done through databricks service principal, you will 
need to create a token for service principal to set up a CLI profile 
https://docs.databricks.com/en/dev-tools/service-principals.html#step-4-generate-a-databricks-personal-access-token-for-the-databricks-service-principal

Update the databricks CLI profile - self.workspace_controler = WorkspaceClient(profile="e2-field")

"""

class UpdateDatabricksWorkflows:
    def __init__(self):
        # Databricks SDK WorkspaceClient
        # Using Databricks CLI profile to access the workspace.
        self.workspace_controler = WorkspaceClient(profile="e2-field-sp")
    
    def get_service_principal(self):
        print(f"INFO: Retrieving service principals...")
        service_principals={}
        all_sps = self.workspace_controler.service_principals.list()
        for sp in all_sps:
            display_name = sp.display_name
            application_id = sp.application_id
            service_principals[display_name] = application_id
        print(f"INFO: Successfully collected all service principals")
        return service_principals

    # List databricks workflows
    def get_workflows(self):
        # Empty dict to collect targeted jobs
        all_jobs = {}

        job_tags = None

        jobs_response = self.workspace_controler.jobs.list(expand_tasks=False)
        for job in jobs_response:
            # Tweak the string in following if condition to pick the desired jobs
            #if "asml test" in job.settings.name.lower():
            job_id = job.job_id
            job_tags = job.settings.tags
            if job_tags is not None and "workload_name" in job_tags:
                workload_name = job_tags['workload_name'] 
                print(f"INFO: Collected tag workload_name: {workload_name} from Workflow ID:{job.job_id}, Workflow Name: {job.settings.name}")
            else:
                print(f"INFO: Tags is None or workload_name tag does not exist in Workflow ID:{job.job_id}, Workflow Name: {job.settings.name}")

            all_jobs[job_id] = workload_name   
        print("INFO: All tags have been collected successfully")      
        return all_jobs

    # Update jobs
    def update_workflow_run_as(self, job_id, service_principal_id):
        try:              
            self.workspace_controler.jobs.update(
                job_id=job_id,
                new_settings=jobs.JobSettings(
                    run_as=jobs.JobRunAs(service_principal_id)
                ),
            )
            return True
        except Exception as e:
            # If an exception is caught, print the error and return False
            print(f"Error updating job: {e}")
            return False


def entrypoint():

    uw = UpdateDatabricksWorkflows()

    # Step 1: Get all service principals available in the workspace
    service_principals = uw.get_service_principal()

    # Step 2: Get all workflows and fetch tag name (workload_name)
    workflows = uw.get_workflows()
    
    print(f"INFO: workflows - {workflows}")
    print(f"INFO: Iisting through workflow dict...\n")

    for workflow_id, workload_name in workflows.items():
        print(f"INFO: Start for Workflow ID: {workflow_id}, {workload_name}")
    
        match_found = False
        # Step 3: Check if service principal contains workload_name and update the job if needed
        for sp_display_name, sp_application_id in service_principals.items():
            if workload_name.lower() in sp_display_name.lower():
                print(f"INFO: Tag workload_name {workload_name} exists in  Service Principal: {sp_display_name}")
                print(f"INFO: Updating run_as for Workflow ID {workflow_id} with Service Principal: {sp_display_name}")
                
                # Update workflow
                status = uw.update_workflow_run_as(workflow_id, sp_application_id)
                
                if status:
                  print(f"INFO: Successfully updated run_as for workflow ID {workflow_id} with Service Principal: {sp_display_name} \n")
                  match_found = True
                  break
                
                else:
                  print(f"ERROR: Failed to updated run_as for workflow ID {workflow_id} with Service Principal: {sp_display_name} \n")
                  match_found = True
                  break

        
        if not match_found:
         print(f"INFO: No matching service principal found for workload_name: {workload_name} \n")

if __name__ == "__main__":
    entrypoint()
