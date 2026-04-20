import { Link, useNavigate, useParams } from 'react-router';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowRight } from 'lucide-react';

import { useAcceptInvitation, useInvitationSummary } from '@/api/invitation';
import { Button } from '@/components/ui/button';
import { LOGIN_ERROR_MSG, useSession } from '@/lib/auth/auth';
import { TooltipProvider, Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip';
import { toast } from 'sonner';

function ViewInvitation() {
    const { id } = useParams();
    const { isLoggedIn } = useSession();
	const { data: invitationData } = useInvitationSummary(id);
    const { mutateAsync: accept } = useAcceptInvitation();
	const navigate = useNavigate();

    if (!id) return <div className="p-6">No invitation to retrieve</div>

	if (!invitationData) return <div className="p-6">No valid invitation found</div>;

    const handleAccept = async () => {
        toast.promise(async () => await accept(id), {
            loading: 'Accepting invitation...',
            success: () => {
                navigate(`/trips/${invitationData.trip_id}`);
                return 'Login successful!';
            },
            error: (err) =>
                `${err instanceof Error ? err.message : LOGIN_ERROR_MSG.DEFAULT}`,
        });
    }

    return (
		<div className="p-6 space-y-6">
            <TooltipProvider>
                <Card>
                    <CardHeader>
                        <CardDescription>You've been invited by{" "}
                            <span>
                                <Tooltip>
                                    <TooltipTrigger className='font-bold'>{invitationData.inviter_name}</TooltipTrigger>
                                    <TooltipContent>{invitationData.inviter}</TooltipContent>
                                </Tooltip>
                            </span>
                        </CardDescription>
                        <CardTitle className="text-3xl font-bold mb-2">{invitationData.trip_name}</CardTitle>
                        <p className="text-muted-foreground">
                            {new Date(invitationData.trip_start).toLocaleString()}{' '}
                            <ArrowRight className="inline mx-1" />
                            {new Date(invitationData.trip_end).toLocaleString()}
                        </p>
                    </CardHeader>
                    <CardContent>
                        {isLoggedIn ? 
                            <div>
                                <Button onClick={handleAccept}>Accept Invitation</Button>
                            </div> 
                            :
                            <div>
                                <CardDescription>
                                    <Link className='text-blue-500 hover:underline' to={`/login/accept-invitation__${id}`}>Log in</Link> to accept the invitation
                                </CardDescription>
                            </div>
                        }
                    </CardContent>
                </Card>
            </TooltipProvider>
        </div>
    )
}

export default ViewInvitation;
