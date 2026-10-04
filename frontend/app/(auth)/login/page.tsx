import { LoginScreen } from "@/components/features/auth/login-screen";

interface LoginPageProps {
  searchParams: Promise<{ next?: string }>;
}

/** Staff sign-in route with a safe post-login destination. */
export default async function LoginPage({
  searchParams,
}: LoginPageProps): Promise<React.JSX.Element> {
  const { next } = await searchParams;
  return <LoginScreen requestedPath={next} />;
}
