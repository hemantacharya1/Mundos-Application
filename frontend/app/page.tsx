import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  ArrowRight,
  Brain,
  Target,
  Zap,
  Shield,
  BarChart3,
  Users,
  CheckCircle,
  Star,
  TrendingUp,
  Clock,
  MessageSquare,
} from "lucide-react"
import Link from "next/link"

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 glass-card border-b border-border/50">
        <div className="w-full max-w-7xl mx-auto px-4 lg:px-6 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Brain className="h-8 w-8 text-primary" />
            <span className="text-xl font-bold">AI Leads</span>
          </div>
          <div className="hidden md:flex items-center space-x-8">
            <a href="#features" className="text-muted-foreground hover:text-foreground transition-colors">
              Features
            </a>
            <a href="#benefits" className="text-muted-foreground hover:text-foreground transition-colors">
              Benefits
            </a>
            <a href="#testimonials" className="text-muted-foreground hover:text-foreground transition-colors">
              Reviews
            </a>
            <a href="#pricing" className="text-muted-foreground hover:text-foreground transition-colors">
              Pricing
            </a>
          </div>
          <Link href="/dashboard">
            <Button>Get Started</Button>
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-20">
        <div className="aurora-bg absolute inset-0 opacity-20" />
        <div className="relative w-full max-w-7xl mx-auto px-4 lg:px-6 py-24 text-center">
          <Badge className="mb-6 bg-primary/10 text-primary border-primary/20">
            🚀 Now Processing 10M+ Leads Monthly
          </Badge>
          <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            AI Powered Lead Management
          </h1>
          <p className="text-xl md:text-2xl text-muted-foreground mb-8 max-w-3xl mx-auto">
            Transform your lead qualification process with intelligent AI that understands, nurtures, and converts
            prospects automatically. <span className="text-primary font-semibold">Increase conversions by 340%</span>
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <Link href="/dashboard">
              <Button size="lg" className="text-lg px-8 py-6 group">
                Start Free Trial
                <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Link>
            <Button size="lg" variant="outline" className="text-lg px-8 py-6 bg-transparent">
              Watch Demo
            </Button>
          </div>
          <div className="flex items-center justify-center space-x-8 text-sm text-muted-foreground">
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              <span>No Credit Card Required</span>
            </div>
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              <span>14-Day Free Trial</span>
            </div>
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              <span>Setup in 5 Minutes</span>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-card/30">
        <div className="w-full max-w-7xl mx-auto px-4 lg:px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-4xl font-bold text-primary mb-2">340%</div>
              <div className="text-muted-foreground">Conversion Increase</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-primary mb-2">10M+</div>
              <div className="text-muted-foreground">Leads Processed</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-primary mb-2">2.5x</div>
              <div className="text-muted-foreground">Faster Qualification</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-primary mb-2">99.9%</div>
              <div className="text-muted-foreground">Uptime SLA</div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24">
        <div className="w-full max-w-7xl mx-auto px-4 lg:px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">Intelligent Lead Processing</h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Our AI doesn't just collect leads—it understands them, qualifies them, and delivers them ready to convert
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              {
                icon: Brain,
                title: "AI-Powered Qualification",
                description:
                  "Advanced AI analyzes lead behavior and intent to prioritize high-value prospects automatically.",
                highlight: "95% accuracy",
              },
              {
                icon: Target,
                title: "Smart Lead Scoring",
                description: "Dynamic scoring based on engagement patterns, company data, and conversion probability.",
                highlight: "Real-time updates",
              },
              {
                icon: Zap,
                title: "Instant Handoff",
                description: "Seamless transition from AI to human agents when leads are ready to convert.",
                highlight: "< 30 seconds",
              },
              {
                icon: Shield,
                title: "Quality Assurance",
                description: "Built-in validation ensures only qualified leads reach your sales team.",
                highlight: "Zero spam",
              },
              {
                icon: BarChart3,
                title: "Advanced Analytics",
                description: "Comprehensive insights into lead performance and conversion metrics.",
                highlight: "50+ metrics",
              },
              {
                icon: Users,
                title: "Team Collaboration",
                description: "Unified workspace for sales teams to manage and track lead progress.",
                highlight: "Unlimited users",
              },
            ].map((feature, index) => (
              <Card key={index} className="glass-card hover:bg-card/70 transition-all duration-300 group">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <feature.icon className="h-12 w-12 text-primary group-hover:scale-110 transition-transform" />
                    <Badge variant="secondary" className="text-xs">
                      {feature.highlight}
                    </Badge>
                  </div>
                  <h3 className="text-xl font-semibold mb-3">{feature.title}</h3>
                  <p className="text-muted-foreground">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section id="benefits" className="py-24 bg-card/30">
        <div className="w-full max-w-7xl mx-auto px-4 lg:px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">Why Choose AI Lead Management?</h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Stop losing qualified leads to slow response times and manual processes
            </p>
          </div>
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div className="space-y-8">
              <div className="flex items-start space-x-4">
                <div className="bg-primary/10 p-3 rounded-lg">
                  <TrendingUp className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold mb-2">Increase Revenue by 340%</h3>
                  <p className="text-muted-foreground">
                    Our AI identifies high-intent leads 5x faster than traditional methods, ensuring you never miss a
                    hot prospect.
                  </p>
                </div>
              </div>
              <div className="flex items-start space-x-4">
                <div className="bg-primary/10 p-3 rounded-lg">
                  <Clock className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold mb-2">Save 15+ Hours Weekly</h3>
                  <p className="text-muted-foreground">
                    Automate lead qualification, scoring, and routing. Your team focuses on closing deals, not sorting
                    leads.
                  </p>
                </div>
              </div>
              <div className="flex items-start space-x-4">
                <div className="bg-primary/10 p-3 rounded-lg">
                  <MessageSquare className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold mb-2">24/7 Lead Engagement</h3>
                  <p className="text-muted-foreground">
                    AI never sleeps. Engage prospects instantly, qualify them automatically, and hand off warm leads to
                    your team.
                  </p>
                </div>
              </div>
            </div>
            <div className="relative">
              <Card className="glass-card p-8">
                <div className="text-center">
                  <div className="text-6xl font-bold text-primary mb-4">$2.4M</div>
                  <div className="text-xl font-semibold mb-2">Additional Revenue</div>
                  <div className="text-muted-foreground mb-6">Generated in first 6 months</div>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span>Lead Response Time</span>
                      <span className="text-primary font-semibold">30 seconds</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Qualification Accuracy</span>
                      <span className="text-primary font-semibold">95%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Conversion Rate</span>
                      <span className="text-primary font-semibold">+340%</span>
                    </div>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section id="testimonials" className="py-24">
        <div className="w-full max-w-7xl mx-auto px-4 lg:px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">Trusted by Industry Leaders</h2>
            <p className="text-xl text-muted-foreground">See how companies are transforming their lead management</p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                name: "Sarah Chen",
                role: "VP of Sales, TechCorp",
                company: "TechCorp Solutions",
                content:
                  "AI Lead Management transformed our sales process. We're closing 3x more deals with the same team size.",
                rating: 5,
              },
              {
                name: "Michael Rodriguez",
                role: "CEO, GrowthLabs",
                company: "GrowthLabs Inc",
                content:
                  "The AI qualification is incredibly accurate. We've eliminated 90% of unqualified leads reaching our sales team.",
                rating: 5,
              },
              {
                name: "Emma Thompson",
                role: "Sales Director, ScaleUp",
                company: "ScaleUp Ventures",
                content:
                  "Response times went from hours to seconds. Our lead-to-customer conversion rate increased by 340%.",
                rating: 5,
              },
            ].map((testimonial, index) => (
              <Card key={index} className="glass-card p-6">
                <div className="flex items-center mb-4">
                  {[...Array(testimonial.rating)].map((_, i) => (
                    <Star key={i} className="h-4 w-4 text-yellow-400 fill-current" />
                  ))}
                </div>
                <p className="text-muted-foreground mb-6 italic">"{testimonial.content}"</p>
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
                    <span className="text-primary font-semibold">
                      {testimonial.name
                        .split(" ")
                        .map((n) => n[0])
                        .join("")}
                    </span>
                  </div>
                  <div>
                    <div className="font-semibold">{testimonial.name}</div>
                    <div className="text-sm text-muted-foreground">{testimonial.role}</div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-24 bg-card/30">
        <div className="w-full max-w-7xl mx-auto px-4 lg:px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">Simple, Transparent Pricing</h2>
            <p className="text-xl text-muted-foreground">Choose the plan that scales with your business</p>
          </div>
          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            <Card className="glass-card p-8 relative">
              <div className="text-center">
                <h3 className="text-2xl font-bold mb-4">Starter</h3>
                <div className="text-4xl font-bold mb-2">
                  $99<span className="text-lg text-muted-foreground">/mo</span>
                </div>
                <p className="text-muted-foreground mb-6">Perfect for small teams</p>
                <ul className="space-y-3 mb-8 text-left">
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>Up to 1,000 leads/month</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>AI qualification</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>Basic analytics</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>Email support</span>
                  </li>
                </ul>
                <Button className="w-full">Start Free Trial</Button>
              </div>
            </Card>

            <Card className="glass-card p-8 relative border-primary">
              <Badge className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-primary">Most Popular</Badge>
              <div className="text-center">
                <h3 className="text-2xl font-bold mb-4">Professional</h3>
                <div className="text-4xl font-bold mb-2">
                  $299<span className="text-lg text-muted-foreground">/mo</span>
                </div>
                <p className="text-muted-foreground mb-6">For growing businesses</p>
                <ul className="space-y-3 mb-8 text-left">
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>Up to 10,000 leads/month</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>Advanced AI features</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>Custom integrations</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>Priority support</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>Team collaboration</span>
                  </li>
                </ul>
                <Button className="w-full">Start Free Trial</Button>
              </div>
            </Card>

            <Card className="glass-card p-8 relative">
              <div className="text-center">
                <h3 className="text-2xl font-bold mb-4">Enterprise</h3>
                <div className="text-4xl font-bold mb-2">Custom</div>
                <p className="text-muted-foreground mb-6">For large organizations</p>
                <ul className="space-y-3 mb-8 text-left">
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>Unlimited leads</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>White-label solution</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>Dedicated support</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>Custom AI training</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>SLA guarantee</span>
                  </li>
                </ul>
                <Button variant="outline" className="w-full bg-transparent">
                  Contact Sales
                </Button>
              </div>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24">
        <div className="w-full max-w-7xl mx-auto px-4 lg:px-6">
          <div className="text-center max-w-3xl mx-auto">
            <h2 className="text-4xl font-bold mb-6">Ready to Transform Your Lead Management?</h2>
            <p className="text-xl text-muted-foreground mb-8">
              Join thousands of companies already using AI to qualify, nurture, and convert more leads
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/dashboard">
                <Button size="lg" className="text-lg px-8 py-6 group">
                  Start Your Free Trial
                  <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
                </Button>
              </Link>
              <Button size="lg" variant="outline" className="text-lg px-8 py-6 bg-transparent">
                Schedule Demo
              </Button>
            </div>
            <p className="text-sm text-muted-foreground mt-4">
              No credit card required • 14-day free trial • Setup in 5 minutes
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-12 bg-card/30">
        <div className="w-full max-w-7xl mx-auto px-4 lg:px-6">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <Brain className="h-6 w-6 text-primary" />
                <span className="text-lg font-bold">AI Leads</span>
              </div>
              <p className="text-muted-foreground mb-4">
                Transform your lead management with intelligent AI that converts prospects automatically.
              </p>
              <div className="flex space-x-4">
                <Button size="sm" variant="ghost">
                  Twitter
                </Button>
                <Button size="sm" variant="ghost">
                  LinkedIn
                </Button>
              </div>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Product</h4>
              <ul className="space-y-2 text-muted-foreground">
                <li>
                  <a href="#features" className="hover:text-foreground transition-colors">
                    Features
                  </a>
                </li>
                <li>
                  <a href="#pricing" className="hover:text-foreground transition-colors">
                    Pricing
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    Integrations
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    API
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Company</h4>
              <ul className="space-y-2 text-muted-foreground">
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    About
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    Blog
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    Careers
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    Contact
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Support</h4>
              <ul className="space-y-2 text-muted-foreground">
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    Help Center
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    Documentation
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    Status
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    Privacy
                  </a>
                </li>
              </ul>
            </div>
          </div>
          <div className="border-t border-border mt-8 pt-8 text-center text-muted-foreground">
            <p>© 2024 AI Lead Management. All rights reserved. Built with intelligence.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
