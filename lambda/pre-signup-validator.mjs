/**
 * Cognito Pre-Signup Lambda Trigger
 * Validates that only @uga.edu email addresses can sign up
 * Auto-confirms and auto-verifies UGA emails
 */

export const handler = async (event) => {
    console.log('Pre-signup trigger invoked:', JSON.stringify(event, null, 2));

    const email = event.request.userAttributes.email;

    // Validate email exists
    if (!email) {
        throw new Error('Email address is required');
    }

    // Convert to lowercase for case-insensitive comparison
    const emailLower = email.toLowerCase();

    // Check if email ends with @uga.edu
    if (!emailLower.endsWith('@uga.edu')) {
        throw new Error('Only @uga.edu email addresses are allowed to register for ArchPal');
    }

    // Auto-confirm the user (skip email verification step)
    event.response.autoConfirmUser = true;

    // Auto-verify the email
    event.response.autoVerifyEmail = true;

    console.log('UGA email validated successfully:', email);

    return event;
};
